from flask import render_template, request, session

from ActiveAMT.ActiveAMT_DB import HITDbHandler
from ActiveAMT.ActiveAMT_EVENTS.observable import Observable
from ActiveAMT.ActiveAMT_FLASK import app

hit_db = HITDbHandler()
observable = Observable()


@app.route('/text_hit.html')
def text_hit():
    """
    Shows the template for a HIT of type 'txt'.
    """
    get_url_params(request.args)

    if 'hitId' in session:
        db_hit = hit_db.get_hit_by_id(session['hitId'])
        session['hit_quest'] = db_hit['question']

    return render_template('HITs/text_hit.html', enabled=is_enabled(), hit_info=session, css='HITs/text_hit.css')


@app.route('/pict_hit.html')
def picture_hit():
    """
    Shows the template for a HIT of type 'img'.
    """
    get_url_params(request.args)

    if 'hitId' in session:
        db_hit = hit_db.get_hit_by_id(session['hitId'])
        if 'question' in db_hit:
            session['hit_quest'] = db_hit['question']
        if 'img_src' in db_hit:
            session['img_src'] = db_hit['img_src']

    return render_template('HITs/pict_hit.html', enabled=is_enabled(), hit_info=session, css='HITs/pict_hit.css')


@app.route('/custom_hit.html')
def custom_hit():
    """
    Shows the template for a HIT of type 'html'
    """
    get_url_params(request.args)

    db_hit = None

    if 'hitId' in session:
        db_hit = hit_db.get_hit_by_id(session['hitId'])
        session['vars'] = db_hit['variables']

    return render_template('HITs/Custom/' + db_hit['html'], enabled=is_enabled(), hit_info=session)


@app.route('/getAnswers', methods=['POST'])
def get_answers():
    """
    Collects the answer(s) from a HIT.
    """

    try:
        session['answer'] = str(request.form['answers'])
    except UnicodeEncodeError:
        session['answer'] = unicode(request.form['answers'])

    quest_ans_dict = {}

    # If answer has a ':' in it, we know it was passed back as a flattened dict
    if ':' in session['answer']:

        answers = ""
        first = True

        key_vals = session['answer'].split('/')

        # Start 1 in, end 1 early, and only select every other.
        # This accounts for the leading/trailing space and the comma in the middle
        for pair in key_vals[1:-1:2]:

            split = pair.split(':')

            if first:
                first = False
                answers += "{}:'{}'".format(split[0], split[1])
            else:
                answers = "{}:'{}', ".format(split[0], split[1]) + answers

            quest_ans_dict[split[0]] = split[1]

            session['answer'] = answers

    hit_db.set_answer_for_hit(session['hitId'], session['answer'])

    with observable.lock:
        observable.notify_observers(remaining_tasks=hit_db.get_remaining_hits(),
                                    completed_task=session)

    print("\nHIT[{}] answered! Answer: {}".format(session['hitId'], session['answer'] if not quest_ans_dict else quest_ans_dict))

    return "Thank you for your input!"


def get_url_params(request_args):
    """
    Helper function to extract the parameters from the URL request.
    """
    session['hitId'] = request_args.get('hitId')
    session['assignmentId'] = request_args.get('assignmentId')
    session['workerId'] = request_args.get('workerId')


def is_enabled():
    """
    Helper function to check if the HIT should be submittable
    """
    enabled = ""
    if session['assignmentId'] == 'ASSIGNMENT_ID_NOT_AVAILABLE' or session['assignmentId'] is None:
        enabled = "disabled"

    return enabled
