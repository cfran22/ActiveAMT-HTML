from ActiveAMT import ActiveAMT
import random


def get_rand_img():
    """
    Grabs a random image from unsplash, returning the local url to that image.
    """
    import urllib
    import os
    import glob

    pics = glob.glob('/home/cody_techngs/PycharmProjects/ProjTest/ActiveAMT/ActiveAMT_FLASK/static/images/HITs/rand*')

    for pic in pics:
        os.remove(pic)

    img_name = 'rand_img{}.jpg'.format(random.randint(0, 2000))
    dl_location = os.getcwd() + '/ActiveAMT/ActiveAMT_FLASK/static/images/HITs/' + img_name
    url = 'https://unsplash.it/400/300/?random'
    urllib.urlretrieve(url, dl_location)

    return 'static/images/HITs/{}'.format(img_name)

# Create API class instance

actAMT = ActiveAMT()

# Mock Data

hit_type_init_file = "/home/cody_techngs/PycharmProjects/ProjTest/ActiveAMT/ActiveAMT_CLIB/HITType.init"

pic_tasks = [
    {'type': 'img',
     'question': 'What do you see in this picture?',
     'img_src': get_rand_img()
     }
]

text_tasks = [
    {'type': 'txt',
     'question': 'Why so serious?'},
    {'type': 'txt',
     'question': 'What is "A que hora es?" in English?'},
    {'type': 'txt',
     'question': 'Boxers or boxer briefs?'}
]

# Pick random task selections
ttask = random.randrange(0, len(text_tasks))

tasks = [pic_tasks[0]]

# Call init_tasks from API instance to make the "random" HITs

actAMT.init_tasks(tasks, hit_type_init_file)

