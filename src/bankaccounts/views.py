from django.shortcuts import render
from shared.utils import *
from shared.handle_get import *
from .models import BankAccount, Transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import IntegrityError
import requests
from decimal import Decimal
import datetime
from goal.goal_helper import get_goal_id_name_mapping_for_user
from shared.handle_real_time_data import get_in_preferred_currency, get_preferred_currency
from tasks.tasks import update_bank_acc_bal, upload_bank_account_transactions
from django.core.files.storage import FileSystemStorage
from django.conf import settings


# Create your views here.


def get_accounts(request):
    template = 'bankaccounts/account_list.html'
    context = dict()
    context['users'] = get_all_users()
    user = None
    context['object_list'] = list()
    context['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
    context['user_name_mapping'] = get_all_users()
    balance = 0
    accounts = BankAccount.objects.all()
    as_on = None
    for acc in accounts:
        last_trans = Transaction.objects.filter(account=acc).order_by('trans_date').last()
        last_trans_dt=None
        if last_trans:
            last_trans_dt = last_trans.trans_date
        acc.last_trans_dt = last_trans_dt

        first_trans = Transaction.objects.filter(account=acc).order_by('trans_date').first()
        first_trans_dt=None
        if first_trans:
            first_trans_dt = first_trans.trans_date
        acc.first_trans_dt = first_trans_dt
        acc.preferred_currency_bal = get_in_preferred_currency(float(acc.balance), acc.currency, datetime.date.today())
        context['object_list'].append(acc)
        balance += acc.preferred_currency_bal
        if not as_on:
            as_on = acc.as_on_date
        elif acc.as_on_date:
            as_on = acc.as_on_date if as_on > acc.as_on_date else as_on
    context['as_on_date'] = as_on
    context['curr_module_id'] = 'id_bank_acc_module'
    context['preferred_currency_bal'] = round(balance, 2)
    context['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
    context['user_name_mapping'] = get_all_users()
    context['preferred_currency'] = get_preferred_currency()    
    return render(request, template, context)

def get_transactions(request, id):
    template = 'bankaccounts/transaction_list.html'
    context = dict()
    try:
        acc = BankAccount.objects.get(id=id)
        trans = Transaction.objects.filter(account=acc)
        context['object_list'] = list()
        for t in trans:
            context['object_list'].append(t)
        context['curr_module_id'] = 'id_bank_acc_module'
        context['account_id'] = acc.id
        context['number'] = acc.number
        return render(request, template, context)
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def add_transaction(request,id):
    template = 'bankaccounts/add_transaction.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    try:
        acc = BankAccount.objects.get(id=id)
        if request.method == 'POST':
            try:
                trans_date = request.POST['trans_date']
                notes = request.POST['notes']
                category = request.POST['tran_sub_type']
                trans_type = request.POST['tran_type']
                amount = get_float_or_none_from_string(request.POST['trans_amount'])
                description = request.POST['description']
                Transaction.objects.create(
                    account=acc,
                    trans_type=trans_type,
                    category=category,
                    amount=amount,
                    notes=notes,
                    trans_date=trans_date,
                    description=description
                )
                message = 'Transaction added successfully'
                message_color = 'green'
                update_bank_acc_bal(acc.id)
            except IntegrityError as ie:
                print(f'failed to add transaction {ie}')
                message = 'Failed to add transaction'
                message_color = 'red'
            except Exception as ex:
                print(f'failed to add transaction {ex}')
                message = 'Failed to add transaction'
                message_color = 'red'
        context['message'] = message
        context['message_color'] = message_color
        user_name_mapping = get_all_users()
        context['user'] = user_name_mapping[acc.user]
        context['curr_module_id'] = 'id_bank_acc_module'
        context['account_id'] = acc.id
        context['number'] = acc.number
        context['bank_name'] = acc.bank_name
        return render(request, template, context)

    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))


def add_account(request):
    template = 'bankaccounts/add_account.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    try:
        if request.method == 'POST':
            number = request.POST['number']
            bank_name = request.POST['bank_name']
            start_date = request.POST['start_date']
            user = request.POST['user']
            notes = request.POST['notes']
            currency = request.POST['currency']
            goal = request.POST.get('goal', '')
            if goal != '':
                goal_id = Decimal(goal)
            else:
                goal_id = None
            if start_date == '':
                start_date = None
            else:
                start_date = get_date_or_none_from_string(start_date)
            BankAccount.objects.create(
                number=number,
                bank_name=bank_name,
                start_date=start_date,
                user=user,
                notes=notes,
                goal=goal_id,
                currency=currency,
                balance=0
            )
            message = 'Account added successfully'
            message_color = 'green'
    except IntegrityError as ie:
        print(f'failed to add bank account {ie}')
        message = 'Failed to add account'
        message_color = 'red'
    except Exception as ex:
        print(f'failed to add bank account {ex}')
        message = 'Failed to add account'
        message_color = 'red'
    url = f'https://raw.githubusercontent.com/krishnakuruvadi/portfoliomanager-data/main/currencies.json'
    print(f'fetching from url {url}')
    r = requests.get(url)
    context['currencies'] = list()
    if r.status_code == 200:
        for entry in r.json()['currencies']:
            context['currencies'].append(entry)
    else:
        context['currencies'].append('INR')
        context['currencies'].append('USD')
    context['message'] = message
    context['message_color'] = message_color
    users = get_all_users()
    context['users'] = users
    context['curr_module_id'] = 'id_bank_acc_module'
    return render(request, template, context)


def update_account(request, id):
    template = 'bankaccounts/update_account.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    try:
        ba = BankAccount.objects.get(id=id)
        if request.method == 'POST':
            try:
                number = request.POST['number']
                bank_name = request.POST['bank_name']
                start_date = request.POST['start_date']
                notes = request.POST['notes']
                currency = request.POST['currency']
                goal = request.POST.get('goal', '')
                print(f'goal {goal}')
                if goal != '':
                    goal_id = Decimal(goal)
                else:
                    goal_id = None
                if start_date == '':
                    start_date = None
                else:
                    start_date = get_date_or_none_from_string(start_date)
                ba.number=number
                ba.bank_name=bank_name
                ba.start_date=start_date
                ba.notes=notes
                ba.goal=goal_id
                ba.currency=currency
                ba.save()
                message = 'Account updated successfully'
                message_color = 'green'
                update_bank_acc_bal(ba.id)
            except IntegrityError as ie:
                print(f'failed to update bank account {ie}')
                message = 'Failed to update account'
                message_color = 'red'
            except Exception as ex:
                print(f'failed to update bank account {ex}')
                message = 'Failed to update account'
                message_color = 'red'
        url = f'https://raw.githubusercontent.com/krishnakuruvadi/portfoliomanager-data/main/currencies.json'
        print(f'fetching from url {url}')
        r = requests.get(url)
        context['currencies'] = list()
        if r.status_code == 200:
            for entry in r.json()['currencies']:
                context['currencies'].append(entry)
        else:
            context['currencies'].append('INR')
            context['currencies'].append('USD')
        context['message'] = message
        context['message_color'] = message_color
        user_name_mapping = get_all_users()
        context['user'] = user_name_mapping[ba.user]
        context['number'] = ba.number
        context['currency'] = ba.currency
        context['notes'] = ba.notes
        context['bank_name'] = ba.bank_name
        context['goal'] = ba.goal if ba.goal else ''
        context['goals'] = get_goal_id_name_mapping_for_user(ba.user)
        
        context['curr_module_id'] = 'id_bank_acc_module'
        print(context)
        return render(request, template, context)
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def account_detail(request, id):
    template = 'bankaccounts/account_detail.html'
    context = dict()
    try:
        acc = BankAccount.objects.get(id=id)
        context['curr_module_id'] = 'id_bank_acc_module'
        context['balance_preferred_currency'] = round(get_in_preferred_currency(float(acc.balance), acc.currency, datetime.date.today()), 2)
        goal_name_mapping = get_all_goals_id_to_name_mapping()
        if acc.goal:
            context['goal'] = goal_name_mapping[acc.goal]
        else:
            context['goal'] = None
        user_name_mapping = get_all_users()
        context['user'] = user_name_mapping[acc.user]
        context['preferred_currency'] = get_preferred_currency()
        context['number'] = acc.number
        context['bank_name'] = acc.bank_name
        context['currency'] = acc.currency
        context['as_on'] = acc.as_on_date
        context['start_date'] = acc.start_date
        context['balance'] = acc.balance
        return render(request, template, context)
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def delete_accounts(request):
    BankAccount.objects.all().delete()
    return HttpResponseRedirect(reverse('bankaccounts:account-list'))

def delete_account(request, id):
    try:
        ba = BankAccount.objects.get(id=id)
        ba.delete()
    except BankAccount.DoesNotExist:
        print(f'account with id does not exist {id}')
    return HttpResponseRedirect('../')

def transaction_detail(request, id, trans_id):
    pass

def delete_transactions(request, id):
    try:
        ba = BankAccount.objects.get(id=id)
        Transaction.objects.filter(account=ba).delete()
        update_bank_acc_bal()
        return HttpResponseRedirect(reverse('bankaccounts:get-transactions', args=[str(id)]))
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))


def delete_transaction(request, id, trans_id):
    try:
        ba = BankAccount.objects.get(id=id)
        Transaction.objects.get(account=ba, id=trans_id).delete()
        update_bank_acc_bal(ba.id)
        return HttpResponseRedirect(reverse('bankaccounts:get-transactions', args=[str(id)]))
    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))
    except Transaction.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:get-transactions', args=[str(id)]))

def upload_transactions(request, id):
    template = 'bankaccounts/upload_transactions.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    try:
        acc = BankAccount.objects.get(id=id)
        if request.method == 'POST':
            try:
                uploaded_file = request.FILES['document']
                fs = FileSystemStorage()
                file_locn = fs.save(uploaded_file.name, uploaded_file)
                print(settings.MEDIA_ROOT)
                full_file_path = settings.MEDIA_ROOT + '/' + file_locn
                file_type = request.POST['file_format']
                print(f'Read transactions from file: {uploaded_file} {file_type} {file_locn} {full_file_path}')
                
                upload_bank_account_transactions(full_file_path, acc.bank_name, file_type, acc.number, acc.id)
                message = 'Upload successful. Processing file'
                message_color = 'green'
            except Exception as ex:
                print(f'failed to upload transactions {ex}')
                message = 'Failed to upload transactions'
                message_color = 'red'
        context['message'] = message
        context['message_color'] = message_color
        user_name_mapping = get_all_users()
        context['user'] = user_name_mapping[acc.user]
        context['curr_module_id'] = 'id_bank_acc_module'
        context['account_id'] = acc.id
        context['number'] = acc.number
        context['bank_name'] = acc.bank_name
        return render(request, template, context)

    except BankAccount.DoesNotExist:
        return HttpResponseRedirect(reverse('bankaccounts:account-list'))