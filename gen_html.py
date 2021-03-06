from flask_frozen import Freezer
from flask import Flask, render_template, redirect
from common import html_dir, load_db, chunks, gen_filename, numberize_int, que, location_db, raise_with_printed_args
import collections
app = Flask(__name__)

path_data_dict = {}


@app.route('/')
def top():
    return redirect('/most_stars0001.html')


@app.route('/route_test')
def route_test():
    return 'route_test'


def gen_tags():
    tags = []
    for d in location_db.all():
        tags.extend(d['tags'])
    counted_tagdict = collections.Counter(tags)
    # Counter({'a': 4, 'c': 2, 'b': 1})
    tags_counts = sorted(list(counted_tagdict.items()),
                         key=lambda x: x[1], reverse=True)
    return tags_counts


tags_info = gen_tags()


@app.route('/<path>/')
def index(path):
    headline_menu, tabulated_repos, max_page_num, tags_num = path_data_dict[path]
    pagenation_bar = gen_pagenation_bar(path, max_page_num)
    return render_template(
        'templete.html',
        tags_info=tags_info,
        tags_num=tags_num,
        headline_menu=headline_menu,
        tabulated_repos=tabulated_repos,
        pagenation_bar=pagenation_bar)


@raise_with_printed_args
def gen_pagenation_bar(path, max_page_num):
    if path == 'locations.html':
        return []
    # path="most_stars0001.html"
    current_page = numberize_int(path)
    filename = path.replace(str(current_page).zfill(4) + ".html", "")
    page_nums = gen_page_nums(current_page, max_page_num)
    pagenation_bar = [(num, gen_html_filename(filename, num), not bool(
        num == current_page or num == '...')) for num in page_nums]
    return pagenation_bar


@raise_with_printed_args
def gen_page_nums(current_page, max_page_num):
    middle_page_num = current_page if bool(
        3 <= current_page <= max_page_num - 2) else 3 if current_page < 3 else max_page_num - 2
    n = middle_page_num
    middle_nums = [n - 2, n - 1, n, n + 1, n + 2]
    if middle_nums[0] > 1:
        middle_nums.insert(0, 1)
    if middle_nums[1] > 2:
        middle_nums.insert(1, '...')

    if middle_nums[-1] < max_page_num:
        middle_nums.append(max_page_num)
    if middle_nums[-2] < max_page_num - 1:
        middle_nums.insert(-1, '...')
    middle_nums = [x for x in middle_nums if x ==
                   '...' or 0 < x <= max_page_num]
    return middle_nums


def test_gen_pagenation_bar():
    test_nums = [
        (1, 100),
        (2, 100),
        (3, 100),
        (4, 100),
        (50, 100),
        (96, 100),
        (97, 100),
        (98, 100),
        (99, 100),
        (100, 100),
    ]
    for test_num in test_nums:
        print(test_num)
        print(gen_page_nums(*test_num))
    for test_num in test_nums:
        path = gen_html_filename('most_stars', test_num[0])
        print(test_num)
        print(gen_pagenation_bar(path, test_num[1]))


@raise_with_printed_args
def build_static_files(paths):
    freezer = Freezer(app)
    app.config['FREEZER_RELATIVE_URLS'] = True
    app.config['FREEZER_DESTINATION'] = html_dir
    app.config['FREEZER_DESTINATION_IGNORE'] = ["gifs", ]

    @freezer.register_generator
    def product_url_generator():
        for path in paths:
            print("writing", path)
            yield "/" + path
    freezer.freeze()


def gen_html_filename(filename, page_index):
    if str(page_index) == '0':
        return filename + '.html'
    else:
        return filename + str(page_index).zfill(4) + '.html'


@raise_with_printed_args
def render_static_files():
    for filename, page_index, headline_menu, tabulated_repos, max_page_num, tags_num in iter_page_data():
        print("calculating", filename, page_index)
        path_data_dict[gen_html_filename(filename, page_index)] = (
            headline_menu, tabulated_repos, max_page_num, tags_num)
    paths = list(path_data_dict.keys())
    build_static_files(paths)


@raise_with_printed_args
def iter_page_data():
    """
    *in templete.html*
    for tr_repos in tabulated_repos:
        for filename, tubled_inforows in tr_repost:
            for string,url ,do_herfin tubled_inforow:
    """
    content_tinydb = load_db()
    all_repo = content_tinydb.all()
    all_repo = [r for r in all_repo if r['gif_success']]
    sortkey_dict = {'most_stars': "stargazers_count",
                    'most_forks': "forks",
                    'recently_updated': "updated_at", }
    for filename, headline_menu in iter_headline():
        sortkey = sortkey_dict[filename]
        all_repo.sort(key=lambda repo: repo[sortkey], reverse=True)
        chunked_repos = chunks(all_repo, 9)
        max_page_num = len(chunked_repos)
        for page_index, nine_repo in enumerate(chunked_repos):
            tubled_inforows = [to_tubled_inforow(repo) for repo in nine_repo]
            tabulated_repos = chunks(tubled_inforows, 3)
            yield filename, page_index + 1, headline_menu, tabulated_repos, max_page_num, 30
    sortkey = "stargazers_count"
    all_repo.sort(key=lambda repo: repo[sortkey], reverse=True)
    user_tags_dict = {d['username'].lower(): d['tags']
                      for d in location_db.all()}
    # print(user_tags_dict.keys())
    tag_users_dict = {}
    for username, tags in user_tags_dict.items():
        for tag in tags:
            tag_users_dict.setdefault(tag, []).append(username)
    user_repos_dict = {}
    for repo in all_repo:
        username = repo['full_name'].split('/')[0].lower()
        # print(username)
        user_repos_dict.setdefault(username, []).append(repo)
    for tag, count in tags_info:
        usernames = tag_users_dict[tag]
        tag_repos = []
        for username in usernames:
            tag_repos.extend(user_repos_dict.get(username, []))
            # print(username)
        chunked_repos = chunks(tag_repos, 9)
        max_page_num = len(chunked_repos)
        for page_index, nine_repo in enumerate(chunked_repos):
            tubled_inforows = [to_tubled_inforow(repo) for repo in nine_repo]
            tabulated_repos = chunks(tubled_inforows, 3)
            yield 'location-' + tag, page_index + 1, deactivated_headline, tabulated_repos, max_page_num, 30
    yield 'locations', '0', deactivated_headline, [], 1, 9999999


def to_tubled_inforow(repo):
    """for string,url,do_herf in tubled_inforow"""
    if 'homepage' not in repo:
        print(repo)
        raise
    tubled_inforow = []
    username = repo['full_name'].split('/')[0]
    tubled_inforow.append(
        ('name:' + username, "", False))
    tubled_inforow.append(
        ('repo:' + repo['full_name'].split('/')[1], repo['html_url'], True))
    tubled_inforow.append(('portfolio website', repo['homepage'], True))
    tubled_inforow.append(
        (f"{repo['stargazers_count']} stars", repo['html_url'] + '/stargazers', True))
    tubled_inforow.append(
        (f"{repo['forks']} forks", repo['html_url'] + '/network/members', True))
    tubled_inforow.append(
        ("updated:" + str(repo['updated_at'])[:10], '', False))
    gif_filename = gen_filename(repo['full_name'])
    location_db_hitdata = location_db.search(que.username == username)
    location_tags = location_db_hitdata[0]['tags'] if location_db_hitdata else list(
    )
    td = [gif_filename, tubled_inforow, location_tags]
    return td


headline_menus_strings_keys = [('Most stars', "most_stars"),
                               ('Most forks', "most_forks"), ('Recently updated', "recently_updated"), ]
deactivated_headline = [(url + '0001.html', key, False)
                        for key, url in headline_menus_strings_keys]


def iter_headline():
    # {"full_name":"itsdpm\/itsdpm.github.io","html_url":"https:\/\/github.com\/itsdpm\/itsdpm.github.io","description":"Website hosted at -- ","created_at":"2017-12-10T10:48:16Z","updated_at":"2017-12-10T13:39:21Z","size":1,"stargazers_count":0,"watchers_count":0,"forks":0,"watchers":0,"score":4.102341,"gif_success":true}
    for iter_key, url in headline_menus_strings_keys:
        headline_menu = [(url + '0001.html', key, bool(key == iter_key))
                         for key, url in headline_menus_strings_keys]
        yield url, headline_menu


def test_build_static_files():
    paths = ['/a/', '/b/']
    build_static_files(paths)


def test_app():
    import os
    print(app.root_path)
    app.root_path = os.path.join(os.path.dirname(
        app.root_path), 'umihico.github.io')
    print(app.root_path)
    app.run(port=12167)


if __name__ == "__main__":
    # test_app()
    # test_build_static_files()
    # test_gen_pagenation_bar()
    render_static_files()
