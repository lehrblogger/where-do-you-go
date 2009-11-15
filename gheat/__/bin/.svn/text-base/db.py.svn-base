#!/usr/local/bin/python
"""Update the database from the txt/csv file.

First run "__/bin/db.py create", then run this script without arguments: it 
should find the points.txt and points.db files.

"""
import csv
import os
import sqlite3
import stat
import sys
from datetime import datetime

import aspen
aspen.configure()


__all__ = ['clear', 'count', 'delete', 'sync']


RAWPATH = os.path.join(aspen.paths.__, 'var', 'points.txt')
DBPATH = os.path.join(aspen.paths.__, 'var', 'points.db')


def _create():
    cur = CONN.cursor()
    cur.execute("""

        CREATE TABLE IF NOT EXISTS points(

            uid         TEXT UNIQUE PRIMARY KEY             ,
            lat         REAL                                ,
            lng         REAL                                ,

            modtime     TIMESTAMP                           ,
            seentime    TIMESTAMP

        );

    """)


def clear():
    cur = CONN.cursor()
    cur.execute("DELETE FROM points")


def count():
    cur = CONN.cursor()
    cur.execute("SELECT COUNT(uid) FROM points")
    print cur.fetchone()[0]


def delete():
    os.remove(DBPATH)


def sync():
    """Synchronize points.db with points.txt.
    """

    sys.stdout.write('syncing'); sys.stdout.flush()

    cur = CONN.cursor()
    modtime = datetime.fromtimestamp(os.stat(RAWPATH)[stat.ST_MTIME])

    for point in csv.reader(open(RAWPATH, 'r')):

        # Parse and validate values.
        # ==========================

        uid, lat, lng = point
        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            print "bad line:", point


        # Select any existing record for this point.
        # ==========================================
        # After this, 'point' will either be None or a sqlite3.Row.

        result = cur.execute("SELECT * FROM points WHERE uid = ?", (uid,))
        result = result.fetchall()
        numresults = len(result) if (result is not None) else 0
        if numresults not in (0, 1):
            msg = "%d result[s]; wanted 0 or 1" % numresults
            print >> sys.stderr, "bad record: <%s> [%s]" % (uid, msg)
        point = result[0] if (numresults == 1) else None


        # Insert the point if we don't have it.
        # =====================================

        if point is None:
            sys.stdout.write('O'); sys.stdout.flush()
            cur.execute("""

                INSERT INTO points
                            (uid, lat, lng, modtime, seentime)
                     VALUES (  ?,   ?,   ?,        ?,    ?)

            """, (uid, lat, lng, modtime, modtime))


        # Update the point if it has changed.
        # ===================================

        elif (point['lat'], point['lng']) != (lat, lng):
            sys.stdout.write('o'); sys.stdout.flush()
            #print (point['lat'], point['lng']), '!=', (lat, lng)

            cur.execute("""

                UPDATE points
                   SET lat = ?
                     , lng = ?
                     , modtime = ?
                     , seentime = ?
                 WHERE uid = ?

            """, (lat, lng, modtime, modtime, uid))


        # If it hasn't changed, at least mark it as seen.
        # ===============================================
        # Otherwise we will delete it presently.

        else:
            sys.stdout.write('.'); sys.stdout.flush()
            cur.execute( "UPDATE points SET seentime = ? WHERE uid = ?"
                       , (modtime, uid)
                        )


    # Now delete rows that weren't in the latest txt file.
    # ====================================================

    cur.execute("DELETE FROM points WHERE seentime != ?", (modtime,))

    print 'done'


if __name__ == '__main__':

    try:
        subc = sys.argv[1]
    except IndexError:
        subc = 'sync' # default

    if subc not in __all__:
        raise SystemExit("I wonder, what does '%s' mean?" % subc)


    # Connect and execute
    # ===================
    # The connect() call will create the database if it doesn't exist. If it was
    # created (i.e., it didn't exist before connect()), we also need to create 
    # the initial table. Since _create() only creates the table if it doesn't
    # exist, and the little extra db hit doesn't affect performance here, we
    # just call _create() every time.

    need_table = os.path.isfile(DBPATH)
    CONN = sqlite3.connect(DBPATH)
    CONN.row_factory = sqlite3.Row # gives us key access
    if subc != 'delete':
        _create() # sets up our table if needed
    func = globals()[subc]
    func()
    CONN.commit()
    CONN.close()

