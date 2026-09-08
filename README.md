# You Post
<br>
> YouPost is a social media website based on this video tutorial(https://www.youtube.com/watch?v=xSUm6iMtREA)
with a few extra features.
This project was made with tools such as Django, HTML & CSS, and JavaScript, with also using PostgeSQL as its primary database.
<br>

## Extra Features
<br>
### 1: 
Users can either like or dislike a post, and they can even
change to switch back again.

### 2:
Users can also add comments to a paticular post, but also
they can edit or delete their own comments as well.

### 3: 
Not only photos can be uploaded, but also videos as well IF
their file types are allowed(.jpeg,.png,.jpg,.mp4 and .mov) and they are less than
20 MB in size.

### 4:
Users can also report posts from other users if they are
inappropiate or for any valid reason.
These reports then get sent to the database for managers to view them;
deciding weather to ban that user or not.

### 5:
Managers of the website can also ban users on the site for
a certain peroid of time with a given reason for them.

## Setup
<br>
1. Clone this repo:
``YouPost``

2. Create and activate a virtual environment (recommended):
``python -m venv .venv
source .venv/bin/activate``

3. Install dependencies:
  ``pip install -r requirements.txt``

4. Apply database migrations:
``python manage.py migrate``

5. (Optional) Create an admin user:
``python manage.py createsuperuser``

6. Run the server:
``python manage.py runserver``

7. Visit the app at http://127.0.0.1:8000/
