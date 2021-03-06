from scraping import url_to_gif, gen_chrome
from api import iter_repo
import pprint
from common import html_dir, load_db, gen_filename, content_tinydb, que
import os


def _updatable_repo_iter(que):
    for repo in iter_repo():
        db_repos = content_tinydb.search(que.html_url == repo['html_url'])
        if not db_repos:
            print('new!', repo['full_name'])
            yield repo
            continue

        db_repo = db_repos[0]
        filename = html_dir + gen_filename(repo['full_name'])
        if not os.path.exists(filename):
            print('not exists!', repo['full_name'])
            yield repo
            continue
        if _conv_updated_at_comparable(repo['updated_at']) > _conv_updated_at_comparable(db_repo['updated_at']):
            print('update!', repo['full_name'])
            yield repo
        else:
            print("already done!", repo['full_name'])


def _conv_updated_at_comparable(raw_updated_at):
    # raw_updated_at = "2011-01-26T19:06:43Z"
    updated_at = tuple([int(s) for s in raw_updated_at[:10].split('-')])
    # updated_at = (2011,1,26)
    return updated_at


def download_all():
    chrome = gen_chrome()
    for repo in _updatable_repo_iter(que):
        do_upsert = True
        portfolio_url = repo['homepage']

        filename = html_dir + gen_filename(repo['full_name'])
        try:
            url_to_gif(portfolio_url, filename, chrome)
        except KeyboardInterrupt as e:
            do_upsert = False
            raise
        except Exception as e:
            # pprint.pprint(repo)
            repo['gif_success'] = False
            error_detail = str(e)
            print(error_detail)
            repo['error_detail'] = error_detail
        else:
            repo['gif_success'] = True
        if do_upsert:
            content_tinydb.upsert(_reduce_amount(
                repo), que.html_url == repo['html_url'])


def _reduce_amount(repo):
    keys = ["html_url", 'description', "size", 'stargazers_count',
            'watchers_count', 'forks', 'watchers', 'score', 'full_name', 'created_at', 'updated_at', 'gif_success', 'error_detail']
    return {k: v for k, v in repo.items() if k in keys}


def optional_edit_content_tinydb():
    # url = 'derekargueta/Personal-Site'
    # content_tinydb.remove(que.full_name == url)
    # hit_repos = raw_api_repos.search(que.full_name == full_name)
    # print(hit_repos[0]['full_name'])
    # print(hit_repos[0]['html_url'])
    all_repo = content_tinydb.all()
    for repo in all_repo:
        if 'homepage' not in repo:
            print(repo['html_url'])
            content_tinydb.remove(que.html_url == repo['html_url'])


if __name__ == '__main__':
    optional_edit_content_tinydb()
    # download_all()
