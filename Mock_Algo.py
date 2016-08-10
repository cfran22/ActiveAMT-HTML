import random

from ActiveAMT import ActiveAMT, Observer

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

                          Mock HITs

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
        },
        {  # From cub batch-0-3.csv, first 3 lines
            'type': 'html',
            'path': '/home/cody_techngs/PycharmProjects/ProjTest/img_triplet.html',
            'fname': 'fname_test',
            'variables': {
                'aurl0': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Corvus_ossifragus_Everglades.jpg/200px-Corvus_ossifragus_Everglades.jpg',
                'burl0': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Ovenbird_RWD2011b.jpg/200px-Ovenbird_RWD2011b.jpg',
                'curl0': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/Yellow-Breasted-Chat-Oregon.jpg/200px-Yellow-Breasted-Chat-Oregon.jpg',
                'abc0': 'Ovenbird',
                'acb0': 'Yellow+breasted+Chat',
                'aurl1': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Brown_Pelican21K.jpg/200px-Brown_Pelican21K.jpg',
                'burl1': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Northern_Cardinal_Broadside.jpg/200px-Northern_Cardinal_Broadside.jpg',
                'curl1': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Western_Grebe_swimming.jpg/200px-Western_Grebe_swimming.jpg',
                'abc1': 'Cardinal',
                'acb1': 'Western+Grebe',
                'aurl2': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Black-throated_blue_warbler_%28Setophaga_caerulescens%29_male.jpg/200px-Black-throated_blue_warbler_%28Setophaga_caerulescens%29_male.jpg',
                'burl2': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Glaucous-winged_gull.jpg/200px-Glaucous-winged_gull.jpg',
                'curl2': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/HoodedOriole.jpg/200px-HoodedOriole.jpg',
                'abc2': 'Glaucous+winged+Gull',
                'acb2': 'Hooded+Oriole',
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

tasks = [all_tasks['html_tasks'][3]]
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
# actAMT.register_observer(ActiveAlgoObserver())

# Initialize the minimum number of tasks
print("\nIn MOCK ALGO....")
print("\tInitializing queue with {} tasks".format(min_tasks))
# for x in range(min_tasks):
#    new_task = make_rand_task()
#    tasks.append(new_task)

actAMT.init_tasks(tasks, hit_type_init_file)
del tasks[:]
