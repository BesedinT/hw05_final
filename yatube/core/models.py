from django.db import models


class Pub_dateModel(models.Model):
    pub_date = models.DateTimeField(
        'Дата',
        auto_now_add=True
    )

    class Meta:
        abstract = True
