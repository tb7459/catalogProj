Description:
   This is a small website application that will allow users to add books to my library.  User account is created using Google login, and once logged in, a user can view and add books to the library.  New Genres can be added, and if the genre is empty(no books), it can be deleted by any logged in user.  Only books added by the user can be removed.  Page is available to users not logged in, but only show book information, once logged in, owner information is displayed as well.

Prerequisites:

--- Virtual Machine ---

download virtual machine: https://www.virtualbox.org/wiki/Downloads - follow directions on page

Install Vagrant: https://www.vagrantup.com/downloads.html

Download configuration: https://d17h27t6h515a5.cloudfront.net/topher/2017/August/59822701_fsnd-virtual-machine/fsnd-virtual-machine.zip


--- Project Files --- 
clone repository to pc:

open git bash 

$ git clone https://github.com/tb7459/catalogProj.git

you should see:
Cloning into 'catalogProj'...
remote: Counting objects: 33, done.
remote: Compressing objects: 100% (25/25), done.
remote: Total 33 (delta 5), reused 30 (delta 5), pack-reused 0
Unpacking objects: 100% (33/33), done.

cd into catalogProj directory
$ cd catalogProj

cd into vagrant
$ cd vagrant

cd into catalog directory
$ cd catalog

vagrant up
login using: vagrant ssh

once logged in
cd /vagrant

--- Application setup ---

set up database with initial values:
vagrant@vagrant:/vagrant$ python lotsofbooks.py

start up application.py
vagrant@vagrant:/vagrant$ python application.py

--- Website ---

The website is running and you can browse to 
http://localhost:5000/library/ in browser of choice

Use the buttons on the left to navigate to the different Genres, and have their books displayed.  Once logged in, a user can add new genres and add new books.  If a new Author is required, this can be done from the add new book link. Login/Logout buttons are found on the top right corner of the page.  Enjoy!!!

---API---

http://localhost:5000/library/<bookId>/JSON, where <bookId> is the integer id of a book.
(http://localhost:5000/library/1/JSON) will return book information for book id = 1
