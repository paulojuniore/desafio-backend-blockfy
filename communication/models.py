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
  visualizado = models.BooleanField(default=False)
  stream = models.ForeignKey(
    'PixStream', 
    on_delete=models.CASCADE, 
    related_name='messages', 
    null=True, 
    blank=True
  )

class PixStream(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  is_active = models.BooleanField(default=True)
  ispb = models.CharField(max_length=8)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
