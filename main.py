import getpass, urllib.parse
from myUFV import myUFV, InvalidLogin
def valid_username(username):
		try:
			if len(username) != 9: raise ValueError
			int(username)
		except ValueError:
				print("Invalid Username")
		else: return True


def main():
		print("Welcome to myUFV-cli")
		is_logged_in = True
		while(is_logged_in):
			print("Please login: ")
			while(True):
				username = input("Enter your myUFV username [nine-digit]: ")
				if valid_username(username): break
			password = urllib.parse.quote_plus(getpass.getpass(prompt='Enter your myUFV password: '))
			print("Please wait, logging in")
			obj_my_ufv = myUFV(username, password)
			try:
				obj_my_ufv.login()
				print("Hi, {}.".format(obj_my_ufv.name.split(" ")[0]))
				print(f"You're logged in.\nName: {obj_my_ufv.name}")
				while(True):
					print("Select an option below: ")
					print("Option ID\tDescription")
					for option in obj_my_ufv.menu:
						print("-\t{}\t{}".format(option, obj_my_ufv.menu[option]))
					_in = int(input(f"Enter option id - [1-{len(obj_my_ufv.menu)}]: "))

					if _in is 1: obj_my_ufv.get_registered_courses()
					if _in is -1:
						print("Bye!")
						exit(0)
			except InvalidLogin:
				print("Incorrect login or session expired")
				continue
			else: break

		


if __name__ == "__main__":
	main()