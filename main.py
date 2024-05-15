import subprocess
import sys

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_dependencies():
    required_packages = ["requests", "Pillow"]
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            install_package(package)
            missing_packages.append(package)
    return missing_packages

if __name__ == "__main__":
    check_dependencies()

from tkinter import Listbox, Tk, Label, Entry, font as tkFont, messagebox, simpledialog
import requests
import webbrowser
from tkinter import ttk
import os
import sqlite3
from PIL import Image, ImageTk

def createTable():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT)''')
    conn.commit()
    conn.close()

def insert_name(username):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

def get_last_users(num_users):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT username FROM users ORDER BY ROWID DESC LIMIT ?", (num_users,))
    last_users = [row[0] for row in c.fetchall()]
    conn.close()
    return last_users

class ConfigurationWindow: 
    def __init__ (self, title, resizable, width, height):
        self.title = title
        self.resizable = resizable
        self.width = width
        self.height = height

class ConfigurationLabel:
    def __init__(self, master, text, font=None):
        self.master = master
        self.text = text
        self.font = font

class ConfigurationEntry:
    def __init__ (self, master, width, font=None, default_text=None, height=None):  
        self.master = master
        self.width = width
        self.font = font
        self.default_text = default_text
        self.height = height  

class ConfigurationButton:
    def __init__(self, master, text, command=None, font=None):
        self.master = master
        self.text = text
        self.command = command
        self.font = font

def configuration_window(window, config):
    window.title(config.title)
    window.resizable(*config.resizable)
    window.geometry(f"{config.width}x{config.height}")

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    window.geometry(f"{width}x{height}+{x}+{y}")

def createLabel(config, textBold=False):
    label = Label(config.master, text=config.text, fg="#ffcc00", bg="#000000")
    if config.font:
        label_font = tkFont.Font(family=config.font, size=14)  
        if textBold:
            label_font.config(weight="bold")
        label.config(font=label_font)
    return label

def createEntry(config):
    entry = Entry(config.master, width=config.width, bg="#000000", fg="#ffcc00")
    if config.font:
        entry_font = tkFont.Font(family=config.font, size=14)  
        entry.config(font=entry_font)
    if config.default_text:
        entry.insert(0, config.default_text)
    return entry 

def clearEntry(event):
    event.widget.delete(0, 'end')  

def getAllRepositories(username):
    global all_repositories 
    all_repositories = []
    page = 1

    while True:
        url = f"https://api.github.com/users/{username}/repos?page={page}&per_page=100"
        response = requests.get(url)
        if response.status_code == 200:
            repositories = response.json()
            if len(repositories) == 0:
                break  
            all_repositories.extend(repositories)
            page += 1
        else:
            break

    return all_repositories

def getUsername():
    global username

    username = entry.get()
    if username:
        if username not in last_users_listbox.get(0, 'end'):
            insert_name(username)
            last_users_listbox.insert("end", username)
        
        repositories = getAllRepositories(username)
        if repositories:
            showRepositories(repositories)
            error_label.config(text="")
        else:
            error_label.config(text=f"No repositories found for user '{username}'")
    else:
        error_label.config(text="Please enter a username.")        

def showRepositories(repositories):
    for repo in repositories:
        if repo["name"]:
            tree.insert('', 'end', values=(repo["name"], "Go to Repo"), tags=("button",))
    if not repositories:
        messagebox.showerror("Warning", "No repositories found for this user.")        

def on_btn_click(event):
    if tree.selection():
        item = tree.selection()[0]
        repo_name = tree.item(item, "values")[0]
        if messagebox.askyesno("Confirmation", f"Do you want to go to the repository '{repo_name}'?"):
            url = f"https://github.com/{entry.get()}/{repo_name}.git"
            webbrowser.open(url)
    else:
        return

def refreshRecentUsers():
    last_users_listbox.delete(0, 'end')  
    last_users = get_last_users(5)  
    if last_users:
        for user in last_users:
            last_users_listbox.insert("end", user)
    else:
        last_users_listbox.insert("end")

def refreshTable():
    entry.delete(0, 'end')

    for item in tree.get_children():
        tree.delete(item)

    username = entry.get()
    if username:
        url = f"https://api.github.com/users/{username}/repos"
        response = requests.get(url)
        if response.status_code == 200:
            repositories = response.json()
            showRepositories(repositories)
    refreshRecentUsers()             

def cloningRepositories():
    if tree.selection():
        item = tree.selection()[0]
        repo_name = tree.item(item, "values")[0]
        username = entry.get()

        if username:
            git_url = f"https://github.com/{username}/{repo_name}.git"
            destination_dir = os.path.join("C:\\Github", repo_name) 

            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
            
            subprocess.run(["git", "clone", git_url, destination_dir])

            os.startfile(destination_dir)
        else:
            messagebox.showinfo("No Selection", "Please select a repository.")   

def on_listbox_double_click(event):
    selected_index = last_users_listbox.curselection()
    if selected_index:
        selected_user = last_users_listbox.get(selected_index[0])
        entry.delete(0, 'end')  
        entry.insert(0, selected_user)  

def clearRecentUsers():
    last_users_listbox.delete(0, 'end')

    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("DELETE FROM users")
    conn.commit()
    conn.close()

def filterRepositories(event):
    global all_repositories

    query = entrySearchRepositorie.get().lower()

    for item in tree.get_children():
        tree.delete(item)

    found = False
    for repo in all_repositories:
        if repo["name"].lower().startswith(query):
            tree.insert('', 'end', values=(repo["name"], "Go to Repo"), tags=("button",)) 
            found= True

        if not found:
            error_label.config(text="No repositories found for this user.")
            error_label.place(x=200, y=130)     
        else:
            error_label.config(text="")           

def open_github(event):
    webbrowser.open("https://github.com/lucascampos04")   

def restore_default_text_username(event):
    if not entry.get():
        entry.insert(0, "Username here")

def restore_default_text_username_repo(event):
    if not entry.get():
        entry.insert(0, "Search Repositorie")

def main():
    global entry, tree, last_users_listbox, entrySearchRepositorie, button_refresh, error_label

    width = 800
    height = 600 

    config = ConfigurationWindow("Github", (False, False), width, height)

    window = Tk()
    configuration_window(window, config)
    center_window(window, width, height)

    # Background
    window.configure(bg="#000000")

    # Imagem
    image = Image.open("github.png")  
    width, height = 40, 40
    resized_image = image.resize((width, height))  

    tk_image = ImageTk.PhotoImage(resized_image)

    image_label = Label(window, image=tk_image, bg="#000000")
    image_label.place(x=755, y=1)

    # Título e entrada de usuário
    config_title_label = ConfigurationLabel(window, "Repositories", font="Fixedsys") 
    titleLabel = createLabel(config_title_label, textBold=True)
    titleLabel.place(x=350, y=20)

    config_entry = ConfigurationEntry(window, width=25, font="Fixedsys", default_text="Username here", height=22)  
    entry = createEntry(config_entry)
    entry.bind("<FocusOut>", restore_default_text_username)
    entry.bind("<FocusIn>", clearEntry)  
    entry.place(x=200, y=70)

    config_search_repositorie = ConfigurationEntry(window, width=25, font="Fixedsys", default_text="Search Repositorie", height=22)
    entrySearchRepositorie = createEntry(config_search_repositorie)
    entrySearchRepositorie.bind("<FocusIn>", clearEntry)
    entrySearchRepositorie.bind("<FocusOut>", restore_default_text_username_repo)
    entrySearchRepositorie.bind("<KeyRelease>", filterRepositories)
    entrySearchRepositorie.place(x = 200, y= 100)

    image_label.bind("<Button-1>", open_github)
    # Botões
    config_button = ConfigurationButton(window, "Search", command=lambda: window.after(100, getUsername), font="Fixedsys")  
    button = ttk.Button(config_button.master, text=config_button.text, command=config_button.command)
    button.place(x=420, y=75)

    refresh_button = ConfigurationButton(window, "Refresh", command=lambda: window.after(100, refreshTable), font="Fixedsys")
    button_refresh = ttk.Button(refresh_button.master, text=refresh_button.text, command=refresh_button.command)
    button_refresh.place(x=710, y=190)
    
    clear_button = ConfigurationButton(window, "Clear Recents", command=lambda: window.after(100, clearRecentUsers), font="Fixedsys")
    clear_refresh = ttk.Button(clear_button.master, text=clear_button.text, command=clear_button.command)
    clear_refresh.place(x=710, y=270)

    cloning_button = ConfigurationButton(window, "Cloning", command=lambda: window.after(100, cloningRepositories), font="Fixedsys")
    cloning_refresh = ttk.Button(cloning_button.master, text=cloning_button.text, command=cloning_button.command)
    cloning_refresh.place(x=710, y=230)

    # Lista de usuários recentes
    last_users_frame = ttk.LabelFrame(window, text="Last Searched Users", style="Retro.TLabelframe")
    last_users_frame.place(x=10, y=10, width=150, height=100)

    last_users_listbox = Listbox(last_users_frame, font=('Fixedsys', 11), selectmode="single", borderwidth=0, border=None, bg="#333333", fg="#ffcc00")
    last_users_listbox.pack(fill="both", expand=True)

    last_users = get_last_users(5)
    if last_users:
        for user in last_users:
            last_users_listbox.insert("end", user)
    else:
        last_users_listbox.insert("end")  

    
    # Tabela de repositórios
    tree = ttk.Treeview(window, columns=("Repositories",), show="headings", height=20, style="Retro.Treeview") 
    tree.heading("#1", text="Repositories")
    tree.column("#1", width=600)  
    tree.place(x=100, y=150)  

    # Estilo
    style = ttk.Style(window)
    style.configure("Retro.Treeview", font=('Fixedsys', 12), background="#333333", foreground="#ffcc00")  
    style.configure("Retro.Treeview.Heading", font=('Fixedsys', 14, 'bold'), background="#333333", foreground="#ffcc00") 
    style.layout("Retro.Treeview", [('Retro.Treeview.treearea', {'sticky': 'nswe'})])  

    tree.tag_configure("button", foreground="#00ffff", font=("Fixedsys", 10, "underline"))
    tree.tag_bind("button", "<Button-1>", on_btn_click)

    style.configure("Retro.TButton", background="#ffcc00", foreground="#000000", padding=10)
    style.map("Retro.TButton", background=[("active", "#ffff00")])

    button.configure(style="Retro.TButton")
    last_users_listbox.bind("<Double-Button-1>", on_listbox_double_click)

    # Label para exibir mensagens de erro
    error_label = Label(window, text="", fg="red", font=("Fixedsys", 12), bg="#333333")
    error_label.place(x=200, y=300) 
    
    window.mainloop()
main()
