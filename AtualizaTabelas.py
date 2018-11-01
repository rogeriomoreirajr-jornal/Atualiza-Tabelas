# coding: latin-1

import requests
import requests.packages.chardet
from operator import attrgetter
import re
import urllib2
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from lxml import etree
from functools import reduce
from datetime import date, timedelta, datetime
import requests_cache
import unicodedata
import os
from time import sleep

## os.environ["REQUESTS_CA_BUNDLE"] = r"S:\# Rob\xf4s\Tabelas\# script\cacert.pem"
os.chdir('\\\\172.20.0.45\\jornalismo novo\\# Robôs\Tabelas\# script')
os.environ["REQUESTS_CA_BUNDLE"] = r"cacert.pem"
s = requests.Session()
senha = open(u'\\\\172.20.0.45\\jornalismo novo\_Utilit\xe1rios\password.txt').read()

pat = 'https://api.globoesporte.globo.com/tabela/{uuid}/fase/{fase}/rodada/{rodada}/jogos/'.format


proxy = ({
    'http':'http://rogerio.moreira:{}@172.20.0.75:8080'.format(senha),
	'https':'https://rogerio.moreira:{}@172.20.0.75:8080'.format(senha)
	})

def make_soup(url):
    html = s.get(url, proxies=proxy, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36'})
    return BeautifulSoup(html.content, "lxml")

def tag(string):
	string = re.sub('^ ','',string)
	string = re.sub(' $','',string)
	string = re.sub(' ','-',string.lower())
	return string

def strip_accents(s):
	s = ''.join(c for c in unicodedata.normalize('NFD', s)
		if unicodedata.category(c) != 'Mn')
	return re.sub('(^ | $)', '',s).lower()

site = 'http://globoesporte.globo.com/futebol/campeonato/'

camp_soup = make_soup(site)

campeonatos = {strip_accents(el.a.text):el.a['href']
				for el in camp_soup.findAll('li', {'itemprop':'itemListElement'})
				if 'href' in el.a.attrs}



class Formula1():
	def __init__(self, debug = False):
		if not debug:
			print 'Checando... formula 1',

		self.site_f1_corrida = "http://ergast.com/api/f1/current/last/results"
		self.site_f1_geral = "http://ergast.com/api/f1/current/driverStandings"
		self.nome = "formula_1"
		self.parent_xml = etree.SubElement(root, "formula_1")
		self.corrida()
		self.resultados_corrida()
		self.resultado_geral()

		if not debug:
			print 'ok'


	dict_countries = {
		'British':'GBR',
		'German':'ALE',
		'Australian':'AUT',
		'Mexican':'MEX',
		'French':'FRA',
		'Spanish':'ESP',
		'Russian':'RUS',
		'Swedish':'SUE',
		'Brazilian':'BRA',
		'Danish':'DIN',
		'Canadian':'CAN',
		'Finnish':'FIN',
		'Belgian':'BEL',
		'Dutch':'HOL',
		'New Zealander':'NZL',
		'Monegasque':'MON'
		}

	dict_countries_race = {
	u'Australia':u'da Austrália',
	u'China':'da China',
	u'Bahrain':'do Bahrein',
	u'Russia':u'da Rússia',
	u'Spain':'da Espanha',
	u'Monaco':u'de Mônaco',
	u'Canada':u'do Canadá',
	u'Azerbaijan':u'do Azerbaijão',
	u'Austria':u'da Aústria',
	u'UK':'do Reino Unido',
	u'Hungary':'da Hungria',
	u'Belgium':u'da Bélgica',
	u'Italy':u'da Itália',
	u'Singapore':'da Cingapura',
	u'Malaysia':u'da Malásia',
	u'Japan':u'do Japão',
	u'USA':'dos Estados Unidos',
	u'Mexico':u'do México',
	u'Brazil':'do Brasil',
	u'UAE':'do Dubai',
	u'Germany':'da Alemanha',
	u'France':u'da França'
	}

	def corrida(self):
		global corrida
		corrida = make_soup(self.site_f1_corrida)
		pais = corrida.find('country').text
		pais = self.dict_countries_race[pais]

		etree.SubElement(self.parent_xml, 'pais').text = pais

	def resultados_corrida(self):
		string_atual = ''
		list_unfinished = []

		resultados = make_soup(self.site_f1_corrida)
		for piloto in resultados.findAll('result'):
			if piloto.find('status')['statusid'] in ['1','11','12','13','14']:
				r = piloto['positiontext']
				n = (' ').join([piloto.driver.givenname.text, piloto.driver.familyname.text])
				c = self.dict_countries[piloto.driver.nationality.text]
				e = piloto.constructor.find('name').text
				if piloto.status.text == u'Finished':
					t = piloto.time.text
				else:
					t = re.sub('Lap','Volta',piloto.status.text)
				linha = ('\t').join([r, n+' ('+c+')', e, t])
				string_atual += linha+'\r'

			else:
				list_unfinished.append((' ').join([piloto.driver.givenname.text, piloto.driver.familyname.text]))

		unfinished = (' e ').join([(', ').join(list_unfinished)[:-1], list_unfinished[-1]]) + u' não finalizaram a corrida'

		etree.SubElement(self.parent_xml, 'corrida').text = string_atual[:-1]
		etree.SubElement(self.parent_xml, 'unfinished').text = unfinished

	def resultado_geral(self):
		string_atual = ''

		standing = make_soup(self.site_f1_geral)
		for piloto in standing.findAll('driverstanding'):
			if piloto['points'] != '0':
				r = piloto['positiontext']
				n = (' ').join([piloto.driver.givenname.text, piloto.driver.familyname.text])
				e = piloto.constructor.find('name').text
				p = piloto['points']

				linha = ('\t').join([r, n, e, p])
				string_atual += linha+'\r'

		etree.SubElement(self.parent_xml, 'standing').text = string_atual[:-1]

class Campeonato():
	def __init__(self, campeonato, debug=False):
		self.json = None
		self.nome = campeonato
		self.parent_xml = etree.SubElement(root,re.sub(' ','-',campeonato))

		self.check(campeonato, debug)


	def check(self, campeonato, debug=False):
		if not debug:
			print 'Checando... {}'.format(campeonato),

		self.soup = make_soup(campeonatos[campeonato])
		self.not_finished = 0
		order = True

		nome_campeonato = self.soup.find('div', 'header-title-content').text

		if self.soup.find('span', 'tabela-navegacao-seletor-ativo'):
			fase = self.soup.find('span', 'tabela-navegacao-seletor-ativo').text
		elif self.soup.find('aside', 'lista-de-jogos'):
			self.rodada = self.soup.find('aside', 'lista-de-jogos')['data-rodada-atual']
			fase = self.rodada+'ª rodada'
		etree.SubElement(self.parent_xml,'nome_campeonato').text = self.title(nome_campeonato)

		"""
		A ideia aqui é conseguir o soup do objeto (o que vai ajudar em alguns casos)
		e definir em que tipo ele entra:
			- Mata a mata normal (jogos no soup)
			- Campeonato com grupos (não sei)
		"""

		if self.soup.find('article','pontos-corridos'):
			"""
			Campeonato normal
			(tabela no soup, jogos no json, atenção para Série B)
			"""
			self.type = 'pontos corridos'
			self.parse_table(soup = self.soup)
			weekday = datetime.today().weekday()
			self.parse_rodada_json()


		elif self.soup.find('article','mata-mata'):
			self.type = 'mata-mata'
			self.fase = self.soup.find('span', 'tabela-navegacao-seletor-ativo').text

			jogos_ida = []
			jogos_volta = []
			self.not_finished = 0

			etree.SubElement(self.parent_xml,'fase').text = self.fase

			chaves = self.soup.findAll('div','chave-jogo-espacador')
			for chave in chaves:
				for jogo in chave.findAll('div','chave-jogo'):
					if 'chave-1-jogos' in jogo['class']:
						jogos_ida.append(self.parse_jogo(jogo.find('div','placar-jogo')))
					elif 'chave-2-jogos' in jogo['class']:
						jogos_ida.append(self.parse_jogo(jogo.findAll('div','placar-jogo')[0]))
						jogos_volta.append(self.parse_jogo(jogo.findAll('div','placar-jogo')[1]))

			output = etree.SubElement(self.parent_xml,'rodada')
			etree.SubElement(output,'cartola').text = u'Jogos de ida'
			etree.SubElement(output,'jogos').text = ('\r').join(sorted(jogos_ida, key = self.sort_data))

			if len(jogos_volta)>0:
				output = etree.SubElement(self.parent_xml,'rodada')
				etree.SubElement(output,'cartola').text = u'Jogos de volta'
				etree.SubElement(output,'jogos').text = ('\r').join(sorted(jogos_volta, key = self.sort_data))



		elif self.soup.find('article','pontos-corridos-grupado'):
			global c
			c = self.soup
			global grupo
			self.type = 'pontos-corridos-grupado'

			for grupo in self.soup.article.findAll('section'):
				self.rodada = grupo.find('aside', 'lista-de-jogos')['data-rodada-atual']
				self.grupo_nome = grupo.find('h2','tabela-header-titulo').text
				nome = tag(re.search(' *(.+) *', grupo.header.text).groups()[0])
				parent_grupo = etree.SubElement(self.parent_xml, nome)
				etree.SubElement(parent_grupo, 'nome').text = re.search(' *(.+) *', grupo.header.text).groups()[0]

				self.parse_table(soup = grupo, output = parent_grupo)
				self.parse_rodada_json(parent = parent_grupo)

		if not debug: print 'ok'


	def title(self, string):
		lista_re = {
			u'brasileir\xe3o s\xe9rie a':u'brasileirão',
			u'brasileir\xe3o s\xe9rie b':u'segundona',
			u'brasileir\xe3o s\xe9rie c':u'série c',
            u'brasileir\xe3o s\xe9rie d':u'série d',
			u'brasileir\xe3o s\xe9rie a'.title():u'brasileirão',
			u'brasileir\xe3o s\xe9rie b'.title():u'segundona',
			u'brasileir\xe3o s\xe9rie c'.title():u'série c',
            u'brasileir\xe3o s\xe9rie d'.title():u'série d',
            u'^ +':'',
            u' $':''
		}

		string = re.sub('(^ | $)','',string)

		if string in lista_re.keys():
			string = lista_re[string]
		return string.title()

	def unfinish(self, parent_xml=None):
		if parent_xml==None: parent_xml = self.parent_xml

		if self.not_finished == 1:
			etree.SubElement(parent_xml,'not_finished').text = u'*Não finalizado até o fechamento desta edição'
		elif self.not_finished > 1:
			etree.SubElement(parent_xml,'not_finished').text = u'*Não finalizados até o fechamento desta edição'
		else:
			etree.SubElement(parent_xml,'not_finished').text = u''


	def sort_data(self, string):
		if re.search('\d+\/\d+, \d+h\t', string):
			s = re.search('\d+\/\d+, \d+h', string).group()
			return datetime.strptime(s, u'%d/%m, %Hh')
		elif re.search('\d+\/\d+, \d+h\d+', string):
			s = re.search('\d+\/\d+, \d+h\d+', string).group()
			return datetime.strptime(s, u'%d/%m, %Hh%M')
		elif re.search('\d+\/\d+', string):
			s = re.search('\d+\/\d+', string).group()
			return datetime.strptime(s, u'%d/%m')
		else: return datetime.today() + timedelta(days=365)


	def check_fim(self, data, horario):
		try:
			data += '/{}'.format(date.today().year)
			if re.match('\d+h$', horario):
				horario += '00'
			ini = datetime.strptime(','.join([data, horario]), '%d/%m/%Y,%Hh%M')

			fim = ini+timedelta(hours=1, minutes=30)
			now = datetime.now()

			if ini.day == now.day and fim > now:
				return True
			else: return False

		except: return False


	def parse_table(self, output = '', soup = ''):
##		global stats

		if output == '':
			output = etree.SubElement(self.parent_xml,'tabela')
		else:
			output = etree.SubElement(output,'tabela')

		if soup == '':
			soup = self.soup

		times = [el.text for el in soup.table.findAll('strong')]
		stats = []

		for linha in soup.find('div', 'tabela-scroll overthrow').tbody.findAll('tr'):
			numeros = [el.text for el in linha.findAll('td') if el.text != u''][:-1]
			stats.append(numeros)

		tab = zip(times, *zip(*stats))

		output.text = '\n'.join([el for el in ['\t'.join(el) for el in tab]])


	def parse_rodada_json(self, parent = None,):
		"""
		Abrir o json, retornar uma string formatada
		"""
		global jogo, json_, soup

		soup = self.soup

		re_json = re.compile('const tUUID = "([^"]+)";?\n +const fase = "([^"]+)"').search
		uuid, fase = re_json(self.soup.find('script',{'id':'scriptReact'}).get_text()).groups()
		json_ = None

		if parent == None: parent=self.parent_xml

		"""
		Preciso usar o json do site, não do call
		"""

		if self.nome in [u'brasileiro serie b',]:
			r = [-1,0]
		else:
			r = [0,1]

		if self.type == 'pontos-corridos-grupado':
			json_re = re.compile(r"const grupos_fase = (.+)\n").search
			json_raw =  json.loads(json_re(self.soup.find('script',{'id':'scriptReact'}).text).groups()[0][:-1])
			json_ = [el for el in json_raw if el['nome_grupo']==self.grupo_nome][0]['lista_jogos']
			r = [0]

		for modifier in r:
			rodada = int(self.rodada)+modifier
			if not self.type == 'pontos-corridos-grupado':
				url_json = pat(uuid=uuid, fase=fase, rodada=rodada)
				json_ = json.loads(make_soup(url_json).text)

			output = etree.SubElement(parent,'rodada')
			etree.SubElement(output,'cartola').text = u'{}ª rodada'.format(rodada)

			l_jogos = []

			for jogo in json_:
##				if self.type == 'pontos-corridos-grupado': jogo = jogo
				d = datetime.strptime(jogo['data_realizacao'],'%Y-%m-%dT%H:%M').strftime('%d/%m')
				h = datetime.strptime(jogo['hora_realizacao'],'%H:%M').strftime('%Hh%M')
				m = jogo['equipes']['mandante']['nome_popular']
				mp = jogo['placar_oficial_mandante']
				if mp == None: mp=''

				vp = jogo['placar_oficial_visitante']
				if vp == None: vp=''

				v = jogo['equipes']['visitante']['nome_popular']

				if jogo['placar_penaltis_mandante']:
					mpp = jogo['placar_penaltis_mandante']
					vpp = jogo['placar_penaltis_visitante']

					dados = [d,h,m,mp,mpp,vpp,vp,v]
					linha = u'{}{}, {}\t{}\t{} ({} x {}) {}\t{}'.format(*dados)

				else:
					dados = [d,h,m,mp,vp,v]
					linha = u'{}, {}\t{}\t{} x {}\t{}'.format(*dados)

				l_jogos.append(linha)

			etree.SubElement(output,'jogos').text = '\n'.join(l_jogos)


	def parse_rodada(self, output = '', soup = None):
		global c
		if not soup:
			url = '/'.join(self.back_url.split('/')[:-1])+'/rodada/{}/jogos.html'
			b_soup = make_soup(url.format(self.rodada))

		parent = self.parent_xml
		rodadas = self.rodadas(soup)

		if self.type == 'grupos':
			rodadas = rodadas[0]
			parent = output

		for rodada in rodadas:
			self.not_finished = 0
			output = etree.SubElement(parent,'rodada')

			if not soup:
				url = '/'.join(self.back_url.split('/')[:-1])+'/rodada/{}/jogos.html'
				soup = make_soup(url.format(rodada))

##			else:
##				c = soup
##				key, = set(soup.find('span','tabela-navegacao-seletor').attrs.keys())&{'data-rodada','data-fase'}
##				rodada = soup.find('span','tabela-navegacao-seletor')[key]

			if soup.find('aside'):
				jogos = soup.find('aside').ul.findAll('li')
			else: jogos = soup.findAll('li')

			l_jogos = []

			for jogo in jogos:
				l_jogos.append(self.parse_jogo(jogo))

			etree.SubElement(output,'cartola').text = u'{}ª rodada'.format(rodada)
			etree.SubElement(output,'jogos').text = '\n'.join(l_jogos)

			self.unfinish(parent_xml=output)


	def parse_jogo(self, jogo):
		global jogo_, dados
		jogo_ = jogo
		data_r = jogo.find('div','placar-jogo-informacoes').text
		ast = ''

		# Jogo adiado?
		try:
			data = re.search('\d{2}\/\d{2}', data_r).group()
		except: data = u''
		try:
			hora = 'h'.join(re.search('(\d{2}):(\d{2})', data_r).groups())
		except:
			hora = ''

		mand = jogo.find('span','placar-jogo-equipes-mandante').find('span','placar-jogo-equipes-nome').text
		visi = jogo.find('span','placar-jogo-equipes-visitante').find('span','placar-jogo-equipes-nome').text

		if self.check_fim(data, hora):
			self.not_finished = True
##			print self.not_finished
			ast = '*'
			m_pl, v_pl = ('','')

		else:
			m_pl = jogo.find('span','placar-jogo-equipes-placar-mandante').text
			v_pl = jogo.find('span','placar-jogo-equipes-placar-visitante').text

		dados = [ast, data, hora, mand, m_pl, v_pl, visi]

		if jogo.findAll('span','placar-jogo-equipes-placar-penalties'):
				m_pn, v_pn = [el.text for el in jogo.findAll('span','placar-jogo-equipes-placar-penalties')]
				dados.insert(5, m_pn)
				dados.insert(6, v_pn)
				linha = u'{}{}, {}\t{}\t{} ({} x {}) {}\t{}'.format(*dados)


		else:
			linha = u'{}{}, {}\t{}\t{} x {}\t{}'.format(*dados)

		return linha

	def rodadas(self, soup):
		global datas, rodadas, rod

		datas_r = [el['content'] for el in soup.findAll('meta', {'itemprop':'startDate'}) if el['content'] != u'']
		datas = sorted(set([datetime.strptime(el, '%Y-%m-%d') for el in datas_r]))

		rod = int(self.rodada)

		# Todas as datas são posteriores a hoje? Hoje é domingo?

		hoje  = datetime.today() - timedelta(hours=4)

		if datetime.today().weekday() == 6:
			if len([el for el in datas if el<hoje])==0:
				rodadas = [str(el) for el in (rod-1, rod)]
			else: rodadas = [str(el) for el in (rod, rod+1)]

		else: rodadas = [str(el) for el in (rod, rod+1)]

		return rodadas

tab = ''

root = etree.Element("root")
stringre = open('dicionario.txt').read()
listare = re.findall('([^\t\n]+)\t([^\t\n]+)', stringre)

listare.extend([['\r0','\n'],
	[', \t','\t'],
	['h00','h'],
	['^0',''],
	('\t\n','\n'),
	('\t\r','\r')])



def limpa_times(text):

	for pat, repl in listare:
		text = re.sub(pat, repl, text, flags=re.MULTILINE | re.UNICODE)
	return text

def view(): print etree.tostring(root, pretty_print = True)
def reset():
	global root
	root = etree.Element("root")

def write(output):
	open(caminho, 'w').write(output)
	print "\n\nTudo certo. Abra os arquivos para atualizá-los."


def master(debug = False):
	lista = [
		u'brasileiro',
		u'brasileiro serie b',
		u'alemao',
		u'ingles',
		u'portugues',
		u'italiano',
		u'frances',
		u'espanhol',
		u'libertadores',
		u'copa do brasil',
		u'liga dos campeoes',
		u'copa sul-americana',
		u'copa santa catarina'
		]

	f = Formula1(debug = debug)

	for el in lista:
##		Campeonato(el, debug = debug)

		try:
			Campeonato(el, debug = debug)
		except:
			print 'erro'

def debug():
	master(debug = True)

def write(filename=''):
   	output = limpa_times(etree.tostring(root, pretty_print = True))
	filename='resultados'
	open('{}.xml'.format(filename), 'w').write(output)

	print "\n\nTudo certo. Abra os arquivos para atualizá-los."

	raw_input()

c = Campeonato('brasileiro')
##
##view()

##if __name__ == '__main__':
##	master()
##	write()
##	view()