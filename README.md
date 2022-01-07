# Instructions

This is a basic ticket management system that I designed and wrote at high school and modified to be published on GitHub in January 2022.

## Setup & Run

This is a [pipenv](https://pipenv.pypa.io/en/latest/) project.

To run the application, simply install Pipenv and then run in your shell:

```shell
$ pipenv sync
$ pipenv run start
```

## Project Structure

This project is mostly made up of a python flask server which renders pages using Jinja2.

The ticket_view page also contains some client-side logic (implemented in TypeScript) to communicate changes to assignee and category with the server asynchronously. You can see the source code for that [here](issue_mgr/static/js/ticket_view.ts)
