# DataCommander
Database submodule for the Commander suite of services.

## Requirements
* [SQLAlchemy](http://www.sqlalchemy.org/)
* [TrueSkill](http://trueskill.org/)

## Usage
1. Add the submodule to a project of your choice.
2. Set the environment variable DATABASE_URL to a database URL understood by SQLAlchemy.
3. Use `Session` and/or `engine` as provided by the module.
