import logging
import os
from logging.config import fileConfig

from flask import current_app

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


def get_metadata():
    from flask import current_app
    with current_app.app_context():
        target_db = current_app.extensions['migrate'].db
        if hasattr(target_db, 'metadatas'):
            return target_db.metadatas[None]
        return target_db.metadata


def active_flask_app():
    try:
        return current_app._get_current_object()
    except RuntimeError:
        return None


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    app = active_flask_app()
    if app is not None:
        config.set_main_option('sqlalchemy.url', get_engine_url())
    elif os.environ.get('OA_DATABASE_URL'):
        config.set_main_option(
            'sqlalchemy.url', os.environ['OA_DATABASE_URL'].replace('%', '%%')
        )
    
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata() if app is not None else None,
        literal_binds=True, version_table_pk=False
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    app = active_flask_app()
    if app is not None:
        # Preserve the Flask-Migrate workflow when invoked by the app CLI.
        with app.app_context():
            def process_revision_directives(context, revision, directives):
                if getattr(config.cmd_opts, 'autogenerate', False):
                    script = directives[0]
                    if script.upgrade_ops.is_empty():
                        directives[:] = []
                        logger.info('No changes in schema detected.')

            conf_args = app.extensions['migrate'].configure_args
            if conf_args.get("process_revision_directives") is None:
                conf_args["process_revision_directives"] = process_revision_directives
            connectable = get_engine()
            metadata = get_metadata()
    else:
        # Standalone Alembic lets an empty DB bootstrap without constructing
        # Flask or invoking application startup side effects.
        section = config.get_section(config.config_ini_section) or {}
        database_url = os.environ.get('OA_DATABASE_URL')
        if database_url:
            section['sqlalchemy.url'] = database_url
        connectable = engine_from_config(
            section, prefix='sqlalchemy.', poolclass=pool.NullPool
        )
        conf_args = {}
        metadata = None

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=metadata,
            version_table_pk=False,
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


# 仅在Alembic上下文中执行，避免在模块导入时执行
def execute_migrations():
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()

# 调用迁移函数
execute_migrations()
