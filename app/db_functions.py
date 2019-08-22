def get_or_default(session, model, default=None, *args, **kwargs):
    instance = find(session, model, *args, **kwargs).first()
    if instance:
        return instance
    return default


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        return create(session, model, **kwargs)


def create(session, model, **kwargs):
    instance = model(**kwargs)
    session.add(instance)
    session.commit()
    return instance


def find(session, model, *args, **kwargs):
    return session.query(model).filter(*args).filter_by(**kwargs)
