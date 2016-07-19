import random

from ActiveAMT import ActiveAMT, Observer

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

                    Create Mock HITs

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

f = open('test.html')
raw_html = f.read()
f.close()

all_tasks = {

    'pic_tasks': [
        {'type': 'img',
         'question': 'Was this picture taken outdoors?',
         'img_src': ''},
        {'type': 'img',
         'question': 'Is there a person in this picture?',
         'img_src': ''},
        {'type': 'img',
         'question': 'Is there a vehicle in this picture?',
         'img_src': ''},
        {'type': 'img',
         'question': 'Is there a body of water in this picture?',
         'img_src': ''}
    ],

    'text_tasks': [
        {'type': 'txt',
         'question': 'Why so serious?'},
        {'type': 'txt',
         'question': 'What is "A que hora es?" in English?'},
        {'type': 'txt',
         'question': 'Boxers or boxer briefs?'},
        {'type': 'txt',
         'question': 'Is the dress blue or grey?'}
    ],

    'html_tasks': [
        {
            'type': 'html',
            'path': '/home/cody_techngs/PycharmProjects/ProjTest/test.html',
            'variables': {
                'q1': "Hello world?",
                'q2': "Testing testing 123. Is this thing on?"
            }
        },
        {
            'type': 'html',
            'raw': raw_html,
            'variables': {
                'q1': "How many pillows is too many?",
                'q2': "What's in the f$#@!ng box?"
            }
        },
        {
            'type': 'html',
            'raw': raw_html,
            'fname': 'random_name',
            'variables': {
                'q1': "Do chickens have large talons?",
                'q2': "Does this CSS make me look fat?"
            }
        }
    ]

}

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

                    Helper Functions

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


def get_rand_img():
    """
    Grabs a random image from unsplash, returning the local url to that image.
    """
    import urllib
    import os
    import glob

    pics = glob.glob('/home/cody_techngs/PycharmProjects/ProjTest/ActiveAMT/ActiveAMT_FLASK/static/images/HITs/rand*')
    nums = []

    for pic in pics:
        nums.append(int(pic.split('rand_img')[1].split('.')[0]))

    unique_num = False
    new_rand_num = 0

    while not unique_num:
        new_rand_num = random.randrange(1, 2000)
        if new_rand_num not in nums:
            unique_num = True

    img_name = 'rand_img{}.jpg'.format(new_rand_num)
    dl_location = os.getcwd() + '/ActiveAMT/ActiveAMT_FLASK/static/images/HITs/' + img_name
    url = 'https://unsplash.it/400/300/?random'
    urllib.urlretrieve(url, dl_location)

    return 'static/images/HITs/{}'.format(img_name)


def make_rand_task():
    """
    Creates a random task of a random type
    """
    rand_type = all_tasks.keys()[random.randint(0, len(all_tasks.keys()) - 1)]
    rand_hit = all_tasks[rand_type][random.randint(0, len(all_tasks[rand_type]) - 1)]

    if rand_hit['type'] == 'img':
        rand_hit['img_src'] = get_rand_img()

    return rand_hit


def add_to_db(task):
    """
    Function that provides mock functionality of adding a received hit to a database
    """
    print("\n\tAdded HIT[{}] to MOCK ALGO database!".format(task['hitId']))


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

                    Actual "Algorithm"

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

hit_type_init_file = "/home/cody_techngs/PycharmProjects/ProjTest/ActiveAMT/ActiveAMT_CLIB/HITType.init"

tasks = []
min_tasks = 3

# Create instance of API
actAMT = ActiveAMT()


class ActiveAlgoObserver(Observer):

    def update(self, *args, **kwargs):
        """
        Function to give to ActiveAMT to be used as callback for each completed HIT
        """

        print("\nIn MOCK ALGO OBSERVER....")

        if 'remaining_tasks' in kwargs:

            remaining_tasks = len(kwargs['remaining_tasks'])

            print("\tThere are {} remaining tasks".format(remaining_tasks))
            print("\tIs {} less than {}? {}".format(remaining_tasks, min_tasks, (remaining_tasks < min_tasks)))

            # If we don't have the minimum number of hits out...
            if remaining_tasks < min_tasks:
                print("\tRefilling queue with {} new task(s)".format(min_tasks - remaining_tasks))
                # Fill up the tasks again
                for t in range(min_tasks - remaining_tasks):
                    new_task = make_rand_task()
                    tasks.append(new_task)

                actAMT.init_tasks(tasks, hit_type_init_file)
                del tasks[:]

        if 'completed_task' in kwargs:
            add_to_db(kwargs['completed_task'])

# Register the observer class with ActiveAMT
actAMT.register_observer(ActiveAlgoObserver())

# Initialize the minimum number of tasks
print("\nIn MOCK ALGO....")
print("\tInitializing queue with {} tasks".format(min_tasks))
for x in range(min_tasks):
    new_task = make_rand_task()
    tasks.append(new_task)

actAMT.init_tasks(tasks, hit_type_init_file)
del tasks[:]
