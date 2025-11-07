from django.db import models
from django.conf import settings

class Dividend(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Dividend for {self.user.username}: {self.amount}"

    class Meta:
        ordering = ['-date']
