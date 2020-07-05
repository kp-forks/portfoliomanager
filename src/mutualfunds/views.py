from django.shortcuts import render
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    ListView,
    DeleteView
)
import datetime
from dateutil.relativedelta import relativedelta
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from shared.utils import *
from shared.handle_get import *
from shared.handle_real_time_data import get_latest_vals, get_forex_rate, get_historical_mf_nav
from django.db import IntegrityError
from .models import Folio, MutualFundTransaction
from common.models import MutualFund
from .kuvera import Kuvera
# Create your views here.

class FolioListView(ListView):
    template_name = 'mutualfunds/folio_list.html'
    queryset = Folio.objects.all()
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        return data

def add_transaction(request):
    template = 'mutualfunds/add_transaction.html'
    if request.method == 'POST':
        folio = request.POST['folio']
        fund = request.POST['fund']
        user = request.POST['user']
        print('user is of type:',type(user))
        trans_date = get_date_or_none_from_string(request.POST['trans_date'])
        trans_type = request.POST['trans_type']
        price = get_float_or_none_from_string(request.POST['price'])
        units = get_float_or_none_from_string(request.POST['units'])
        conversion_rate = get_float_or_none_from_string(request.POST['conversion_rate'])
        trans_price = get_float_or_none_from_string(request.POST['trans_price'])
        broker = request.POST['broker']
        notes = request.POST['notes']
        insert_trans_entry(folio, fund, user, trans_type, units, price, trans_date, notes, broker, conversion_rate, trans_price)
    users = get_all_users()
    context = {'users':users, 'operation': 'Add Transaction'}
    return render(request, template, context)

def insert_trans_entry(folio, fund, user, trans_type, units, price, date, notes, broker, conversion_rate=1, trans_price=None):
    folio_obj = None
    try:
        folio_obj = Folio.objects.get(folio=folio)
    except Folio.DoesNotExist:
        print("Couldnt find folio object:", folio)
        mf_obj = MutualFund.objects.get(code=fund)
        folio_obj = Folio.objects.create(folio=folio,
                                         fund=mf_obj,
                                         user=user,
                                         quantity=0,
                                         buy_price=0,
                                         buy_value=0,
                                         gain=0)
    if not trans_price:
        trans_price = price*units*conversion_rate
    try:
        MutualFundTransaction.objects.create(folio=folio_obj,
                                             trans_date=date,
                                             trans_type=trans_type,
                                             price=price,
                                             units=units,
                                             conversion_rate=conversion_rate,
                                             trans_price=trans_price,
                                             broker=broker,
                                             notes=notes)
        if trans_type == 'Buy':
            new_units = float(folio_obj.units)+units
            new_buy_value = float(folio_obj.buy_value) + trans_price
            folio_obj.units = new_units
            folio_obj.buy_value = new_buy_value
            folio_obj.buy_price = new_buy_value/float(new_units)
            folio_obj.save()
        else:
            new_units = float(folio_obj.quantity)-units
            if new_units:
                new_buy_value = float(folio_obj.buy_value) - trans_price
                folio_obj.units = new_units
                folio_obj.buy_value = new_buy_value
                folio_obj.buy_price = new_buy_value/float(new_units)
                folio_obj.save()
            else:
                folio_obj.delete()
    except IntegrityError:
        print('Transaction exists')

class FolioDetailView(DetailView):
    template_name = 'mutualfunds/folio_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Folio, id=id_)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        data['goal_str'] = get_goal_name_from_id(data['object'].goal)
        data['user_str'] = get_user_name_from_id(data['object'].user)
        return data

class FolioDeleteView(DeleteView):
    template_name = 'mutualfunds/folio_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Folio, id=id_)

    def get_success_url(self):
        return reverse('mutualfund:folio-list')

class FolioTransactionsListView(ListView):
    template_name = 'mutualfunds/transactions_list.html'
    #queryset = Transactions.objects.all()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data)
        id_ = self.kwargs.get("id")
        print("id is:",id_)
        data['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
        data['user_name_mapping'] = get_all_users()
        return data
    
    def get_queryset(self):
        id_ = self.kwargs.get("id")
        print("id is:",id_)
        folio = get_object_or_404(Folio, id=id_)
        return MutualFundTransaction.objects.filter(folio=folio)

class TransactionsListView(ListView):
    template_name = 'mutualfunds/transactions_list.html'
    queryset = MutualFundTransaction.objects.all()

class TransactionDeleteView(DeleteView):
    template_name = 'mutualfunds/transaction_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(MutualFundTransaction, id=id_)

    def get_success_url(self):
        return reverse('mutualfund:transactions-list')

class TransactionDetailView(DetailView):
    template_name = 'mutualfunds/transaction_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(MutualFundTransaction, id=id_)

def upload_transactions(request):
    template = 'mutualfunds/upload_transactions.html'
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    if request.method == 'POST':
        uploaded_file = request.FILES['document']
        user = request.POST['user']
        broker = request.POST.get('brokerControlSelect')
        print(uploaded_file)
        print(broker)
        fs = FileSystemStorage()
        file_locn = fs.save(uploaded_file.name, uploaded_file)
        print(file_locn)
        print(settings.MEDIA_ROOT)
        full_file_path = settings.MEDIA_ROOT + '/' + file_locn
        add_transactions(broker, user, full_file_path)
        fs.delete(file_locn)
    users = get_all_users()
    context = {'users':users}
    return render(request, template, context)

def add_transactions(broker, user, full_file_path):
    if broker == 'KUVERA':
        kuvera_helper = Kuvera(full_file_path)
        for trans in kuvera_helper.get_transactions():
            print("trans is", trans)
            insert_trans_entry(
                trans["exchange"], trans["symbol"], user, trans["type"], trans["quantity"], trans["price"], trans["date"], trans["notes"], 'ZERODHA')

def update_folio(request, id):
    template = 'shares/update_folio.html'
    folio = Folio.objects.get(id=id)
    if request.method == 'POST':
        goal = request.POST['goal']
        share.user = int(request.POST['user'])
        print('user is:',folio.user)
        if goal != '':
            folio.goal = int(goal)
        else:
            folio.goal = None
        notes = request.POST['notes']
        folio.save()
        
    else:
        users = get_all_users()
        context = {'users':users,
                   'folio':folio.folio,
                   'fund_name':folio.fund.name,
                   'user':folio.user,
                   'goal':folio.goal,
                   'notes':folio.notes}
        return render(request, template, context)
    return HttpResponseRedirect("../")

def mf_refresh(request):
    print("inside mf_refresh")
    start = datetime.date.today()+relativedelta(days=-5)
    end = datetime.date.today()
    folio_objs = Folio.objects.all()
    for folio_obj in folio_objs:
        if folio_obj.as_on_date != datetime.date.today():
            vals = get_historical_mf_nav(folio_obj.code, start, end)
            if vals:
                for k, v in vals.items():
                    if k and v:
                        if not folio_obj.as_on_date or k > folio_obj.as_on_date:
                            folio_obj.as_on_date = k
                            folio_obj.latest_price = v
                            #if folio_obj.exchange == 'NASDAQ':
                            #    share_obj.conversion_rate = get_forex_rate(k, 'USD', 'INR')
                            #else:
                            #    share_obj.conversion_rate = 1
                            folio_obj.latest_value = float(folio_obj.latest_price) * float(folio_obj.conversion_rate) * float(share_obj.quantity)
                            folio_obj.save()
        if folio_obj.latest_value: 
            folio_obj.gain=folio_obj.latest_value-folio_obj.buy_value
            folio_obj.save()
    print('done with request')
    return HttpResponseRedirect(reverse('mutualfund:mf-list'))