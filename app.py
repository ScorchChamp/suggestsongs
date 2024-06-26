from flask import Flask, request, jsonify, redirect, make_response, render_template
import datastudy_commons as dsc
import service.loginservice as loginservice
import service.userservice as userservice
import service.spotifyservice as spotifyservice
import service.trackservice as trackservice
import dotenv, os
from waitress import serve

if not os.getenv('PRODUCTION'): dotenv.load_dotenv()

main = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/')

@main.route('/', methods=['GET'])
@dsc.flask.catch_exceptions
def index():
    try:
        user_data = userservice.get_user_data(request.cookies.get('auth_token'))
        if not user_data: return render_template('index.html')
        return render_template('index.html', name=user_data.get('display_name'), email=user_data.get('email'), product=user_data.get('product'))
    except: return render_template('index.html')

@main.route('/feedback', methods=['GET'])
@dsc.flask.catch_exceptions
def feedback():
    try:
        user_data = userservice.get_user_data(request.cookies.get('auth_token'))
        if not user_data: return redirect('/')
        return render_template('feedback.html', name=user_data.get('display_name'), email=user_data.get('email'), product=user_data.get('product'))
    except: return redirect('/')

@main.route('/api/feedback', methods=['POST'])
@dsc.flask.required_form_keys(['feedback'])
@dsc.flask.catch_exceptions
def feedback_post():
    user_id = loginservice.get_user_id(request.cookies.get('auth_token'))
    try: userservice.save_feedback(user_id, request.form.get('feedback'))
    except ValueError as e: return render_template('feedback_error.html', error=str(e))
    return redirect('/feedback_thanks')

@main.route('/feedback_thanks', methods=['GET'])
@dsc.flask.catch_exceptions
def feedback_thanks():
    return render_template('feedback_thanks.html')

@main.route('/login', methods=['GET'])
@dsc.flask.catch_exceptions
def login():
    return redirect(loginservice.get_spotify_auth_url())

@main.route('/callback/spotify', methods=['GET'])
@dsc.flask.required_query_keys(['code'])
@dsc.flask.catch_exceptions
def spotify_callback():
    try: jwt_token = loginservice.login_user(request.args.get('code'))
    except: return "Could not authenticate. Are you added as a tester? Ask Lars for help."
    response = make_response(redirect('/'))
    response.set_cookie('auth_token', jwt_token, max_age=3600)
    user_id = loginservice.get_user_id(jwt_token)
    spotifyservice.get_top_tracks_user(user_id)
    return response

@main.route('/logout', methods=['GET'])
@dsc.flask.catch_exceptions
def logout():
    response = make_response(redirect('/'))
    response.set_cookie('auth_token', '', expires=0)
    return response

@main.route('/api/next-songs', methods=['GET'])
@dsc.flask.catch_exceptions
def next_songs():
    user_id = loginservice.get_user_id(request.cookies.get('auth_token'))
    return jsonify({'data': trackservice.get_next_songs(user_id)})

@main.route('/api/rate-track', methods=['POST'])
@dsc.flask.required_body_keys(['id', 'rating'])
@dsc.flask.catch_exceptions
def rate_track():
    user_id = loginservice.get_user_id(request.cookies.get('auth_token'))
    trackservice.rate_track(user_id, request.json.get('id'), request.json.get('rating'))
    return jsonify({'status': 'ok'})

@main.route('/api/top-rated-songs', methods=['GET'])
@dsc.flask.catch_exceptions
def top_rated_tracks():
    user_id = loginservice.get_user_id(request.cookies.get('auth_token'))
    return jsonify({'data': trackservice.get_top_rated_tracks(user_id)})




if __name__ == '__main__':
    serve(main, host='0.0.0.0', port=os.environ.get('PORT', 80))