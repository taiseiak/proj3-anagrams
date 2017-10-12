"""
Flask web site with vocabulary matching game
(identify vocabulary words that can be made 
from a scrambled string)
"""

import flask
import logging

# Our own modules
from letterbag import LetterBag
from vocab import Vocab
from jumble import jumbled
import config

###
# Globals
###
app = flask.Flask(__name__)

CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY  # Should allow using session variables

#
# One shared 'Vocab' object, read-only after initialization,
# shared by all threads and instances.  Otherwise we would have to
# store it in the browser and transmit it on each request/response cycle,
# or else read it from the file on each request/responce cycle,
# neither of which would be suitable for responding keystroke by keystroke.

WORDS = Vocab(CONFIG.VOCAB)

###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    """The main page of the application"""
    flask.g.vocab = WORDS.as_list()
    flask.session["target_count"] = min(
        len(flask.g.vocab), CONFIG.SUCCESS_AT_COUNT)
    flask.session["jumble"] = jumbled(
        flask.g.vocab, flask.session["target_count"])
    flask.session["matches"] = []
    return flask.render_template('vocab.html')


###############
# AJAX request handlers
#   These return JSON, rather than rendering pages.
###############


@app.route("/_compute")
def compute():
    """
    Computes the input string. To see if the string
    is made from the scramble and if words can be made
    from the bank.
    """
    app.logger.debug("Got a JSON request")

    text = flask.request.args.get("text", type=str)
    jumble = flask.session["jumble"]
    matches = flask.session.get("matches", [])
    app.logger.debug(matches)

    # Text made from jumbled letters
    in_jumble = LetterBag(jumble).contains(text)
    # Text is in words list
    matched = WORDS.has(text)

    text_with_space = text + ' '

    if matched and in_jumble and not (text_with_space in matches):
        # Cool, they found a new word
        matches.append(text_with_space)
        flask.session["matches"] = matches
    elif not matched:
        app.logger.debug("Word is not in the list")
    elif not in_jumble:
        app.logger.debug("Some letters not in jumble")
    else:
        app.logger.debug("This case shouldn't happen!")
        assert False  # Raises AssertionError

    result = {"matches": "".join(matches),
              "found": len(matches) >= flask.session["target_count"]}
    return flask.jsonify(result=result)


#################
# Functions used within the templates
#################

@app.template_filter('filt')
def format_filt(something):
    """
    Example of a filter that can be used within
    the Jinja2 code
    """
    return "Not what you asked for"

###################
#   Error handlers
###################


@app.errorhandler(404)
def error_404(e):
    app.logger.warning("++ 404 error: {}".format(e))
    return flask.render_template('404.html'), 404


@app.errorhandler(500)
def error_500(e):
    app.logger.warning("++ 500 error: {}".format(e))
    assert not True  # I want to invoke the debugger
    return flask.render_template('500.html'), 500


@app.errorhandler(403)
def error_403(e):
    app.logger.warning("++ 403 error: {}".format(e))
    return flask.render_template('403.html'), 403


####

if __name__ == "__main__":
    if CONFIG.DEBUG:
        app.debug = True
        app.logger.setLevel(logging.DEBUG)
    app.logger.info(
        "Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0")
