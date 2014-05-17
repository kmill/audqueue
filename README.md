audqueue
========

A web-based client for queuing music in Audacious.

To install, first pip the requirements.txt file.  Then,
- create a the database with sqlite3 data.db < audqueue.sql
- run updater.do_directory_sync(model.Database("data.db"), music_directory) for each music_directory you have
- ./start
- go to http://localhost:3322

Make sure Audacious is running.
