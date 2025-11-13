from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.renderers import JSONRenderer
from .serializers import PixMessageSerializer
from rest_framework.response import Response
from .models import PixMessage, PixStream
from rest_framework.views import APIView
from datetime import datetime,  timezone
from rest_framework import status
from faker import Faker
import random
import time
import uuid

# Classe para gerar mensagens Pix com dados falsos.
fake = Faker('pt_BR')

MAX_STREAMS_PER_ISPB = 6
MAX_MESSAGES_PER_STREAM = 10
LONG_POLLING_TIMEOUT = 8  # segundos

@method_decorator(csrf_exempt, name='dispatch')
class PixMessageView(APIView):
  
  # Gera mensagens Pix falsas para um determinado ISPB.
  def post(self, request, ispb, number):
    try:
      number = int(number)

      if number <= 0:
        return Response({'error': 'Number parameter must be a positive integer.'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
      return Response({'error': 'Number parameter must be provided.'}, status=status.HTTP_400_BAD_REQUEST)
    
    messages = []
    for _ in range(number):
      pagador_ispb = str(random.randint(10000000, 99999999))
      valor = round(random.uniform(1.00, 1000.00), 2)

      pagador = {
        "nome": fake.name(),
        "cpfCnpj": fake.cpf(),
        "ispb": pagador_ispb,
        "agencia": fake.random_number(digits=4, fix_len=True),
        "contaTransacional": fake.random_number(digits=6, fix_len=True),
        "tipoConta": random.choice(["CACC", "SVGS"])
      }

      recebedor = {
        "nome": fake.name(),
        "cpfCnpj": fake.cpf(),
        "ispb": ispb,
        "agencia": fake.random_number(digits=4, fix_len=True),
        "contaTransacional": fake.random_number(digits=6, fix_len=True),
        "tipoConta": random.choice(["CACC", "SVGS"])
      }

      message = PixMessage.objects.create(
        endToEndId=f"E{ispb}{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}{uuid.uuid4().hex[:6]}",
        pagador=pagador,
        recebedor=recebedor,
        valor=valor,
        dataHoraPagamento=datetime.now(),
        campoLivre="",
        txId=fake.uuid4(),
      )

      messages.append(message)

    serializer = PixMessageSerializer(messages, many=True)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# Renderizador que aceita qualquer tipo de Header e evita o erro 406 (Not Acceptable) ao enviar um Header Accept multipart/json.
class FallbackJSONRenderer(JSONRenderer):
    media_type = '*/*'

class PixStreamStartView(APIView):
  renderer_classes = [FallbackJSONRenderer]

  # Inicia uma nova sessão de stream para obter mensagens Pix.
  def get(self, request, ispb):
    active_streams = PixStream.objects.filter(ispb=ispb, is_active=True)
    if active_streams.count() >= MAX_STREAMS_PER_ISPB:
      return Response({'error': 'Maximum number of active streams reached.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    header = request.headers.get('Accept', 'application/json')
    multiple = header == 'multipart/json'
    
    # Cria uma nova sessão de stream.
    stream_session = PixStream.objects.create(ispb=ispb)

    response = self._get_messages(ispb, stream_session, multiple)
    response["Pull-Next"] = f"/api/pix/{ispb}/stream/{stream_session.id}"
    return response
  
  # Método auxiliar para obter mensagens com long polling.
  def _get_messages(self, ispb, stream, multiple):
    start_time = time.time()
    while time.time() - start_time < LONG_POLLING_TIMEOUT:

      # Busca todas as mensagens não visualizadas.
      all_receiver_messages = PixMessage.objects.filter(recebedor__ispb=ispb, visualizado=False)

      # Restringe o número de mensagens (10 no máximo) retornadas com base no cabeçalho Accept enviado.
      filtered_receiver_messages = list(all_receiver_messages[:10 if multiple else 1])

      # Marca as mensagens como visualizadas para não serem mais retornadas.
      if all_receiver_messages.exists():
        all_receiver_messages \
          .filter(id__in=[msg.id for msg in filtered_receiver_messages]) \
          .update(visualizado=True)

        # Serializa as mensagens e retorna a resposta.
        data = PixMessageSerializer(filtered_receiver_messages, many=True).data   
        return Response(data, status=status.HTTP_200_OK)
      
      # Aguarda um curto período antes de verificar novamente.
      time.sleep(5)
    
    # Se o tempo limite for atingido sem novas mensagens, retorna 204 No Content.
    response = Response(status=status.HTTP_204_NO_CONTENT)
    response["Pull-Next"] = f"/api/pix/{ispb}/stream/{stream.id}"
    return response

  
class PixStreamNextView(APIView):
  renderer_classes = [FallbackJSONRenderer]

  # Obtém as próximas mensagens em uma sessão de stream existente.
  def get(self, request, ispb, interationId):
    stream_session = PixStream.objects.filter(id=interationId, ispb=ispb).first()
    if not stream_session:
      return Response({'error': 'Stream session not found.'}, status=status.HTTP_404_NOT_FOUND)

    header = request.headers.get('Accept', 'application/json')
    multiple = header == 'multipart/json'
    
    response = PixStreamStartView._get_messages(self, ispb, stream_session, multiple)
    response["Pull-Next"] = f"/api/pix/{ispb}/stream/{stream_session.id}"
    return response
  
  # O stream não é removido, apenas marcado como inativo.
  def delete(self, request, ispb, interationId):
    stream_session = PixStream.objects.filter(id=interationId, ispb=ispb).first()
    stream_session.is_active = False
    stream_session.save()
    return Response(data={}, status=status.HTTP_200_OK)
