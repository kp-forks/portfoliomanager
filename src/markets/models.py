from django.db import models

# Create your models here.


class PEMonthy(models.Model):
    index_name = models.CharField(max_length=60)
    month = models.IntegerField(null=False)
    year = models.IntegerField(null=False)
    pe_avg = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    pe_max = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    pe_min = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    class Meta:
        unique_together = (('index_name','month', 'year'),)

class PBMonthy(models.Model):
    index_name = models.CharField(max_length=60)
    month = models.IntegerField(null=False)
    year = models.IntegerField(null=False)
    pb_avg = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    pb_max = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    pb_min = models.DecimalField(max_digits=10, decimal_places=2, null=False)

    class Meta:
        unique_together = (('index_name','month', 'year'),)