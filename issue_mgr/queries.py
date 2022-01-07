from objects import Role


def insert_issue(conn, issue_summary, issue_description, username):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ticket (summary, description, creator) VALUES (?, ?, ?)",
        (issue_summary, issue_description, username)
    )
    conn.commit()

    cursor.execute(
        "SELECT last_insert_rowid() as inserted_rowid"
    )
    return cursor.fetchone()['inserted_rowid']


def get_user_tickets(conn, username):
    """
    Returns all tickets assigned to the user, or unassigned.
    :param conn:
    :param username:
    :return:
    """
    cursor = conn.cursor()
    cursor.execute(
        """SELECT
            ticket_id,
            summary,
            cat.category_id as category_id,
            cat.name as category_name,
            creator,
            creator_usr.role as creator_role,
            assignee
        FROM ticket
            INNER JOIN user as creator_usr on ticket.creator = creator_usr.username
            LEFT JOIN category cat on ticket.category_id = cat.category_id
        WHERE assignee=? OR assignee IS NULL
        ORDER BY ticket_id ASC;""",
        [username]
    )
    return cursor.fetchall()


def get_all_tickets(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            ticket_id,
            summary,
            cat.category_id as category_id,
            cat.name as category_name,
            creator,
            creator_usr.role as creator_role,
            assignee
        FROM ticket
            INNER JOIN user as creator_usr on ticket.creator = creator_usr.username
            LEFT JOIN category cat on ticket.category_id = cat.category_id
        ORDER BY ticket_id ASC;
        """)
    return cursor.fetchall()


def get_ticket_detail(conn, ticket_id):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        ticket_id,
        summary,
        description,
        cat.category_id as category_id,
        cat.name as category_name,
        creator,
        creator_usr.role as creator_role,
        assignee
        FROM ticket
            INNER JOIN user as creator_usr on ticket.creator = creator_usr.username
            LEFT JOIN category cat on ticket.category_id = cat.category_id
        WHERE ticket_id = ?;
    """, [ticket_id])
    return cursor.fetchone()


def get_all_categories(conn):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        category_id,
        name as category_name
    FROM category""")

    return cursor.fetchall()


def set_ticket_category(conn, ticket_id, category_id):
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE ticket
        SET category_id = ?
        WHERE ticket_id = ?;""",
        (category_id, ticket_id)
    )
    return conn.commit()


def get_ticket_category(conn, ticket_id):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT c.name as category_name, c.category_id as category_id
        FROM ticket LEFT JOIN category c on ticket.category_id = c.category_id
        WHERE ticket.ticket_id = ?;""",
        [ticket_id]
    )
    return cursor.fetchone()


def get_all_admins(conn):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        user.username
    FROM user
    WHERE user.role = ?
    ORDER BY user.username ASC;
    """, [Role.admin.value])

    return cursor.fetchall()


def set_ticket_assignee(conn, ticket_id, assignee):
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE ticket
        SET assignee = ?
        WHERE ticket_id = ?""",
        (assignee, ticket_id)
    )
    return conn.commit()


def get_ticket_assignee(conn, ticket_id):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT assignee as username FROM ticket WHERE ticket_id = ?""",
        [ticket_id]
    )
    return cursor.fetchone()


def delete_ticket(conn, ticket_id):
    cursor = conn.cursor()
    cursor.execute("""
    DELETE FROM ticket WHERE ticket_id = ?;
    """, [ticket_id])
    conn.commit()
