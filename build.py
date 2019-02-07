# Stdlib
import json
import os
import os.path, time
from datetime import datetime
import re

# Pypi: mardown2
import markdown2

# Pypi: jinja2
from jinja2 import Template

# Pypi: PyGithub
from github import Github

page_size = 2
output_path = './output/'

html_template = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>%s</title>
</head>
<body>
%s
</body>
</html>
"""


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def prepare_content():
    index_content = []
    path = './content/'

    files = os.listdir(path)

    files = [os.path.join(path, f) for f in files]
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    output_files = os.listdir(output_path)
    for i in output_files:
        os.remove(os.path.join(output_path, i))

    for file_name in files:
        if not file_name.endswith('md'):
            continue

        created = datetime.fromtimestamp(os.path.getctime(file_name)).date()

        with open(file_name) as file:
            output_file_name = file_name.split('/')[-1]
            title = output_file_name[:-3].replace('-', " ").capitalize()

            content = markdown2.markdown(file.read())
            html = html_template % (title, content)

            output_file_name = output_file_name.replace('md', 'html')
            output_file_path = os.path.join(output_path, output_file_name)

            index_content.append(dict(
                url=output_file_name,
                title=title,
                content=re.sub(r'<[^>]*?>', '', content[:128]),
                created=created
            ))
            with open(output_file_path, 'w') as new_file:
                new_file.write(html)

    items = chunks(index_content, page_size)
    with open('./index.html') as index_template:
        template = Template(index_template.read())

        for index, value in enumerate(items):
            file_name = 'page_%s.html' % str(index + 1)
            if not index:
                file_name = 'index.html'
            index_output_file = os.path.join(output_path, file_name)
            with open(index_output_file, 'w') as file:
                file.write(template.render(
                    articles=value,
                    pragination=range(1, page_size + 1),
                    current_page=index + 1
                ))


def migrate_github():
    with open('./settings.json', 'r') as setting_file:
        settings = json.loads(setting_file.read())

    token = settings['github_token']
    g = Github(token)
    repo = g.get_repo(settings['repository'])

    files = os.listdir(output_path)

    contents = repo.get_contents("")

    for file in files:
        output_path_file = os.path.join(output_path, file)
        with open(output_path_file) as output_file:
            if file in [i.path for i in contents]:
                data = {
                    'path': file,
                    'message': 'updated: %s' % datetime.now(),
                    'content': output_file.read(),
                    'sha': next(i.sha for i in contents if i.path == file)
                }
                repo.update_file(**data)
            else:
                data = {
                    'path': file,
                    'message': 'created: %s' % datetime.now(),
                    'content': output_file.read()
                }
                repo.create_file(**data)

    contents_path = [i.path for i in contents]
    different = set(contents_path) ^ set(files)
    for file in different:
        sha = next(i.sha for i in contents if i.path == file)
        repo.delete_file(file, "remove file", sha)


prepare_content()
migrate_github()
