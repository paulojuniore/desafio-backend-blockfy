from rest_framework.test import APITestCase
from faker import Faker

fake = Faker('pt_BR')

class PixStreamAPITestCase(APITestCase):
  def setUp(self):
    # Preenche o banco de dados com 7 mensagens Pix para o ISPB '12345678'.
    self.client.post('/api/util/msgs/12345678/7')

  # Inicia um stream para um ISPB existente e verifica se retorna 200 OK com o cabeçalho Pull-Next.
  def test_start_stream(self):
    headers = {'Accept': 'application/json'}
    response = self.client.get('/api/pix/12345678/stream/start', headers=headers)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.headers['Pull-Next'] is not None, True)

  # Inicia um stream para um ISPB sem mensagens e verifica se retorna 204 No Content.
  def test_start_non_existent_stream(self):
    headers = {'Accept': 'application/json'}
    response = self.client.get('/api/pix/12345677/stream/start', headers=headers)
    self.assertEqual(response.status_code, 204)

  # Inicia um stream para um ISPB com mensagens e verifica se retorna apenas 1 mensagem.
  def test_start_existent_stream_with_application_json_header(self):
    headers = {'Accept': 'application/json'}
    response = self.client.get('/api/pix/12345678/stream/start', headers=headers)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(response.data), 1)

  # Inicia um stream para um ISPB com mensagens e verifica se retorna até 10 mensagens.
  def test_start_existent_stream_with_multipart_header(self):
    headers = {'Accept': 'multipart/json'}
    response = self.client.get('/api/pix/12345678/stream/start', headers=headers)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(response.data), 7)

  # Inicia um stream e obtém apenas uma mensagem, e em seguida obtém as próximas com o stream ID
  ## e header multipart/json.
  def test_get_next_messages(self):
    header_request = {'Accept': 'application/json'}
    start_response = self.client.get('/api/pix/12345678/stream/start', headers=header_request)
    header_response = start_response.headers['Pull-Next']
    stream_id = header_response.split('/')[-1]

    header_multipart = {'Accept': 'multipart/json'}
    next_response = self.client.get(f'/api/pix/12345678/stream/{stream_id}', headers=header_multipart)
    self.assertEqual(next_response.status_code, 200)
    self.assertEqual(len(next_response.data), 6)

  # Tenta iniciar mais streams do que o permitido para um ISPB e verifica se retorna 429 Too Many Requests.
  def test_max_streams_per_ispb(self):
    stream1 = self.client.get('/api/pix/12345678/stream/start')
    self.assertEqual(stream1.status_code, 200)
    stream2 = self.client.get('/api/pix/12345678/stream/start')
    self.assertEqual(stream2.status_code, 200)
    stream3 = self.client.get('/api/pix/12345678/stream/start')
    self.assertEqual(stream3.status_code, 200)
    stream4 = self.client.get('/api/pix/12345678/stream/start')
    self.assertEqual(stream4.status_code, 200)
    stream5 = self.client.get('/api/pix/12345678/stream/start')
    self.assertEqual(stream5.status_code, 200)
    stream6 = self.client.get('/api/pix/12345678/stream/start')
    self.assertEqual(stream6.status_code, 200)
    # Tenta iniciar o sétimo stream, que deve falhar.
    stream7 = self.client.get('/api/pix/12345678/stream/start')
    self.assertEqual(stream7.status_code, 429)
    # Verifica a mensagem de erro retornada.
    self.assertEqual(stream7.data['error'], 'Maximum number of active streams reached.')