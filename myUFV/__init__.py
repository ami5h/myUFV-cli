import re, requests
from bs4 import BeautifulSoup
class InvalidLogin(Exception):
	pass
class myUFV:
	url = "https://my.ufv.ca"
	login_url = "https://identity.ufv.ca/commonauth"
	headers = {	
	"User-Agent": "myUFV-cli",
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
	"Accept-Language": "en-CA,en-US;q=0.7,en;q=0.3",
	"Accept-Encoding": "gzip, deflate",
	"Origin": "https",
	"DNT": "1",
	"Connection": "close",
	"X-Requested-With": "XMLHttpRequest",

	}
	
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.session = requests.session()
		self.request = self.session.get(myUFV.url)
		self.session_token = myUFV.__get_session_token(self)
		self.menu = {
			1: "Shows list of courses registered with details with final exam date"
		}
	
	def is_loggedin(func):
		def wrapper(self, *param):
			func(self, *param)
			soup = BeautifulSoup(self.request.text, features="html.parser")
			title_without_session = ["Login with UFV Identity Service".lower(), "login", "identity", "Status - myUFV".lower()]
			if (soup.title.string.lower() in title_without_session):
				raise InvalidLogin("Incorrect password or session expired")
		return wrapper

	def __get_session_token(self):
		return re.compile('sessionDataKey\=([A-Za-z0-9-]+)').search(self.request.url)[1]
	@is_loggedin
	def login(self):
		headers = myUFV.headers
		headers["Content-Type"] = "application/x-www-form-urlencoded"
		login_data = f"username={self.username}&password={self.password}&sessionDataKey={self.session_token}"
		self.request = self.session.post(myUFV.login_url, headers = headers, data = login_data)
		try: self.name = BeautifulSoup(self.request.text, features="html.parser").find('a', {'class': 'user-fullname use-dialog'}).string.strip()
		except AttributeError: pass

	def __get_term_id(self):
		self.cookies = {
		"JSESSIONID": re.compile('JSESSIONID\=([A-Z0-9]+)').search(self.request.request.headers['Cookie'])[1],
		"BIGipServermyportal": re.compile('BIGipServermyportal\=([0-9.]+)').search(self.request.request.headers['Cookie'])[1],
		"GUEST_LANGUAGE_ID": "en_US",
		"COOKIE_SUPPORT": "TRUE"
		}
		self.p_auth = re.findall(r"p_auth\=([A-Za-z0-9]+)", self.request.text)[2]
		myUFV.headers['Referer'] = "https://myportal.ufv.ca/"
		url = "https://myportal.ufv.ca/web/home-community/1?p_auth={}&p_p_id="\
		"CompositeCoursesPortlet_WAR_luminis&p_p_lifecycle=1&p_p_state=exclusive&p_p_mode=view&p_p_col_id="\
		"column-2&p_p_col_pos=6&p_p_col_count=8&actions=1&indexNumber=0&selectedTermId=null".format(self.p_auth)
		self.request = self.session.get(url, headers = myUFV.headers, cookies = self.cookies)
		soup = BeautifulSoup(self.request.text, features="html.parser")
		option_tag = soup.find_all('option')
		term_id = {}
		i = 1
		for tag in option_tag:
			term_id[i] = {'id': option_tag[i-1]['id'], 'name': option_tag[i-1].string.strip(),
			"tt_url": f"https://www.ufv.ca/arfiles/includes/{option_tag[i-1]['value']}-timetable-with-changes.htm",
			"fe_url": f"https://www.ufv.ca/arfiles/includes/{option_tag[i-1]['value']}-exam-schedule.htm" }
			i+=1
		self.term_id = term_id
	@is_loggedin
	def get_registered_courses(self):
		myUFV.__get_term_id(self)
		print("Term ID\tTerm Name")
		for id in self.term_id:
			print(f"{id}\t{self.term_id[id]['name']}")
		try:
			user_input = int(input(f"Please enter the term id [1-{len(self.term_id)}]: "))
			if user_input < 1 and user_input > len(self.term_id): raise ValueError
		except ValueError:
			print("Invalid option selected!")
			exit(1)
		url = 'https://myportal.ufv.ca/web/home-community/1?p_auth={}&p_p_id=CompositeCoursesPortlet_WAR_luminis&'\
		'p_p_lifecycle=1&p_p_state=exclusive&p_p_mode=view&controlPanelCategory='\
		'portlet_CompositeCoursesPortlet_WAR_luminis&actions=2&selectedTermId={}&indexNumber=0'.format(self.p_auth, self.term_id[user_input]['id'])
		self.request = self.session.post(url, headers = myUFV.headers, cookies = self.cookies)
		courses = myUFV.__parse_courses(self.request.text)
		myUFV.__get_fe_date(self, courses, str(self.term_id[user_input]['fe_url']))
		for course in courses:
			print(f"Course CRN: {course}\nCourse Name: {courses[course]['name']}\nSection: {courses[course]['section']}\n"\
			f"Instructor Name:{courses[course]['instructor']}\nInstructor\'s Email: {courses[course]['email']}")
			try: print(f"Final Exam: {courses[course]['fe_date']}")
			except KeyError: pass
			try: print(f"Course Schedule: {courses[course]['tt_date']}")
			except KeyError: pass
			print("\n")

	def __parse_courses(req):
		soup = BeautifulSoup(req, features="html.parser")
		_tmp = soup.tbody.tr
		i = 1
		courses = {}
		while(_tmp):
			[crn, tid] = _tmp.find(lambda tag: tag.name == 'td' and tag.get('class') == ['tableRtBorder'])['id'].split(".")
			courses[crn] = {"name": _tmp.find('td', {"class": "tableRtBorder tableText"}).string.strip()}
			courses[crn]["section"] = _tmp.find(lambda tag: tag.name == 'td' and tag.get('class') == ['tableRtBorder']).string.strip()
			courses[crn]["instructor"] = _tmp.find('td', {"width": "100%"}).string.strip()
			courses[crn]["email"] = _tmp.find('td', {"style":"vertical-align:middle"}).a["href"].split(":")[1].strip()
			courses[crn]["tid"] = tid
			_tmp = _tmp.find_next_sibling('tr')
		return courses
	

	def __get_fe_date(self, courses, url):
		self.request = self.session.get(url)
		if self.request.status_code != 200:
			return
		soup = BeautifulSoup(self.request.text, features="html.parser")
		for c in courses:
			_tmp = soup.find('tr', {'height': '20'})
			strr = ""
			while(_tmp):
				course_block = _tmp.find(lambda tag: tag.name == 'td' and tag.string == c)
				if not course_block: 
					_tmp = _tmp.find_next_sibling('tr')
					continue
				_tmp2 = _tmp.td
				flag = False
				while(_tmp2):
					if _tmp2.string == c:
						for i in ["On "," at ", " in "]:
							_tmp2 = _tmp2.find_next_sibling('td')
							strr += i
							strr += _tmp2.string
							flag = True
					if flag: break
					_tmp2 = _tmp2.find_next_sibling('td')
				_tmp = _tmp.find_next_sibling('tr')
			courses[c]["fe_date"] = strr if strr else "Yayy! no exam"