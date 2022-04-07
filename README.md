The code and the readme are adapted from the repository https://github.com/inb-luebeck/ml_deep_learning_challenge_app

# Running this Dash application on Heroku

You'll need a Github and Heroku account. This [guide](https://towardsdatascience.com/deploying-your-dash-app-to-heroku-the-magical-guide-39bd6a0c586c) is very helpful, as well as the [Dash documentation](https://dash.plotly.com/deployment).

You can test your app locally using gunicorn (which will be used by Heroku as well). Thus, run:
```
gunicorn app:server -b :8000
```
You can find your app using a browser at the address http://0.0.0.0:8000/.

If the app is running fine locally you can move it to a Heroku server. The first time,
you'll need to run:
```
heroku create my-dash-app 
```
"my-dash-app" is the name of your app which you can change to any name. However, only lowercase strings are allowed.

Next, run:
```
git push heroku master # deploy code to heroku
heroku ps:scale web=1  # run the app with a 1 heroku "dyno"
```

## Writing Files to your dropbox folder

Heroku servers restart and thus loose any files that are not committed to Github every 24 hours. As a workaround you can download and upload data files to Dropbox.

You can create an access token [here](https://www.dropbox.com/developers/apps).

* Click on "create app"
* In permissions, you'll need to enable "files.content.write"
* All paths in dbx.files_upload need to start with "/"
* Click generate an Access Token and save the string somewhere save!

The access token should be loaded via an environment variable. To add a variable
Heroku run
```
heroku config:set ACC_TOKEN=your_token
```

## Other solutions considering file persistency

https://medium.com/geekculture/files-on-heroku-cd09509ed285