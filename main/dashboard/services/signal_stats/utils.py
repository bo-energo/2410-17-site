def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict.
    Assume the column names are unique.

    More info: https://docs.djangoproject.com/en/5.1/topics/db/sql/#executing-custom-sql-directly
    """

    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
