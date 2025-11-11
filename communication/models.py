from django.db import models
import uuid

class PixMessage(models.Model):
  endToEndId = models.CharField(max_length=100, unique=True)
  valor = models.DecimalField(max_digits=10, decimal_places=2)
  pagador = models.JSONField()
  recebedor = models.JSONField()
  campoLivre = models.TextField(blank=True, null=True)
  txId = models.CharField(max_length=50)
  dataHoraPagamento = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.end_to_end_id

class PixStream(models.Model):
  ispb = models.CharField(max_length=8)
  interation_id = models.CharField(max_length=12, unique=True, default='')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def save(self, *args, **kwargs):
    if not self.iteration_id:
        self.iteration_id = uuid.uuid4().hex[:12]
    super().save(*args, **kwargs)