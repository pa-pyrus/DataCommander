#!/usr/bin/python
# vim:fileencoding=utf-8:ts=8:et:sw=4:sts=4:tw=79

"""
common.py: Common objects used by the package and its users.
"""

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import create_engine
from os import environ
engine = create_engine(environ["DATABASE_URL"])

from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)

# don't pollute the namespace when importing
del declarative_base, create_engine, sessionmaker

# simple unit tests
if __name__ == "__main__":
    print("Setting up Unit Test environment...")
    from sqlalchemy import create_engine, func
    engine = create_engine("sqlite://", echo=False)
    Session.configure(bind=engine)
    del Base
    from .models import Base, Player, Game, Patch, Tournament
    Base.metadata.create_all(engine)
    session = Session()
    import trueskill
    from datetime import datetime, timedelta

    # test players
    print("Testing Player class...")
    p100 = Player(100, "Player 100", trueskill.Rating(), datetime.utcnow())
    print(" Player ID:", p100.pid)
    print(" Name:", p100.name)
    print(" TrueSkill:", p100._ts_mu, "-", p100._ts_sigma)
    print(" Rating:", p100.skill, "-", p100.rating)
    print(" Representation:", p100)
    print(" Games:", p100.games)
    r100 = trueskill.Rating(p100._ts_mu*2, p100._ts_sigma/2)
    print("Testing skill setter with", r100)
    p100.skill = r100
    print(" TrueSkill:", p100._ts_mu, "-", p100._ts_sigma)
    print(" Rating:", p100.skill, "-", p100.rating)
    print(" Representation:", p100)
    print("Testing skill setter with", None)
    p100.skill = None
    print(" TrueSkill:", p100._ts_mu, "-", p100._ts_sigma)
    print(" Rating:", p100.skill, "-", p100.rating)
    print(" Representation:", p100)

    print("Adding players...")
    p0 = Player(0, "Player 0", trueskill.Rating(), datetime.utcnow())
    p1 = Player(1, "Player 1", trueskill.Rating(10, 1), datetime.utcnow())
    p2 = Player(2, "Player 2", trueskill.Rating(20, 2), datetime.utcnow())
    p3 = Player(3, "Player 3", trueskill.Rating(30, 3), datetime.utcnow())
    p4 = Player(4, "Player 4", trueskill.Rating(40, 4), datetime(1970, 1, 1))
    print(" Players:", [p0, p1, p2, p3, p4])
    session.add_all([p0, p1, p2, p3, p4])
    session.commit()

    print("Testing player queries...")
    print(" All:", session.query(Player).all())
    print(" ID 1:", session.query(Player).filter(Player.pid == 1).one())
    print(" ID < 3:", session.query(Player).filter(Player.pid < 3).all())
    print(" Name like %3%:",
          (session.query(Player)
           .filter(Player.name.like("%3%"))).one())
    print(" Rating > 20:",
          (session.query(Player)
           .filter(Player.rating > 20).all()))
    print(" Names by desc Rating:",
          (session.query(Player.name)
           .order_by(Player.rating.desc())).all())
    print(" Names older than 1 week:",
          (session.query(Player.name)
           .filter(Player.updated < datetime.utcnow() - timedelta(7)).all()))

    print("Testing Game class...")
    p101 = Player(101, "Player 101", trueskill.Rating(), datetime.utcnow())
    g100 = Game(100, p100, p100, p101)
    print(" Game ID:", g100.gid)
    print(" Winner ID:", g100.wid)
    print(" Winner:", g100.winner)
    print(" Players:", g100.players)
    print(" Representation:", g100)
    print("Testing back references...")
    print(" Winner games:", g100.winner.games)
    print("Testing Draw...")
    g101 = Game(101, None, p100, p101)
    print(" Game ID:", g101.gid)
    print(" Winner ID:", g101.wid)
    print(" Winner:", g101.winner)
    print(" Players:", g101.players)
    print(" Representation:", g101)
    print("Adding a game without players...")
    try:
        Game(102, None)
    except AssertionError:
        print(" Cannot add a game without players.")

    print("Adding a game with not enough players...")
    try:
        Game(102, None, p100)
    except AssertionError:
        print(" Cannot add a game with not at least 2 players.")

    print("Adding a game where winner is not a player...")
    try:
        Game(103, p100, p101)
    except AssertionError:
        print(" Cannot add a game where winner is not a player.")

    print("Adding a game with duplicate players...")
    try:
        Game(104, None, p100, p100)
    except AssertionError:
        print(" Cannot add a game with not enough unique players.")

    print("Adding games...")
    g0 = Game(0, p0, p0, p1)
    g1 = Game(1, p1, p0, p1)
    g2 = Game(2, p1, p1, p0)
    g3 = Game(3, None, p0, p1)
    g4 = Game(4, p0, p0, p1, p2, p3, p4)

    print([g0, g1, g2, g3, g4])
    session.add_all([g0, g1, g2, g3, g4])
    session.commit()

    print("Testing game queries...")
    print(" All:", session.query(Game).all())
    print(" IDs:", session.query(Game.gid).all())
    print(" ID 1:", session.query(Game).filter(Game.gid == 1).one())
    print(" ID < 3:", session.query(Game).filter(Game.gid < 3).all())
    print(" Draws:", session.query(Game).filter(Game.winner is None).all())

    print(" P0 wdl:", p0.wdl)
    print(" P0 sum:", sum(p0.wdl))
    print(" P0 rank:",
          session.query(func.count(Player.pid))
          .filter(Player.rating > p0.rating).scalar())

    # test patches
    from datetime import datetime
    print("Testing Patch class...")
    pStable = Patch("stable", "4711", "Latest Stable Build", datetime.utcnow())
    print(" Patch Name:", pStable.name)
    print(" Build:", pStable.build)
    print(" Description:", pStable.description)
    print(" Updated:", pStable.updated)
    print(" Representation:", pStable)

    print("Adding Patches...")
    pTesting = Patch("PTE", "0815",
                     "Private Test Environment", datetime.utcnow())
    print([pStable, pTesting])
    session.add_all([pStable, pTesting])
    session.commit()

    print("Testing Patch queries...")
    print(" All:", session.query(Patch).all())
    print(" Descriptions:", session.query(Patch.description).all())
    print(" Stable:", session.query(Patch)
                             .filter(Patch.name == "stable").one())
    print(" Testing DT:", session.query(Patch.updated)
                                 .filter(Patch.name == "PTE").one())

    # test tournaments
    print("Testing Tournament class...")
    pKOTP = Tournament("King of the Planet #0", datetime.utcnow(), None,
                       "BO5 King vs Ursurper", "http://example.com",
                       "exodusesports.com/king-of-the-planet-0.json",
                       "0123456789abcdef0123456789abcdef")
    print(" Tournament Title:", pKOTP.title)
    print(" Tournament Date:", pKOTP.date)
    print(" Tournament Winner:", pKOTP.winner)
    print(" Tournament Mode:", pKOTP.mode)
    print(" Tournament URL:", pKOTP.url)
    print(" Tournament Path:", pKOTP.path)
    print(" Tournament Hash:", pKOTP.md5_hash)

    print("Adding Tournaments...")
    t1 = Tournament("Dummy Tournament #1", datetime.utcnow(), None,
                    "Some Mode", "http://example.com",
                    "example.com/dummy-1.json",
                    "0123456789abcdef0123456789abcdef")
    t2 = Tournament("Dummy Tournament #2", datetime.utcnow(), None,
                    "Some Mode", "http://example.com",
                    "example.com/dummy-2.json",
                    "0123456789abcdef0123456789abcdef")
    t3 = Tournament("Dummy Tournament #3", datetime.utcnow(), "Winner",
                    "Some Mode", "http://example.com",
                    "example.com/dummy-3.json",
                    "0123456789abcdef0123456789abcdef")
    session.add_all([t1, t2, t3])
    session.commit()

    print("Testing Tournament queries...")
    print(" All:", session.query(Tournament).all())
    print(" Titles:", session.query(Tournament.title).all())
    print(" Winners:", session.query(Tournament)
                              .filter(Tournament.winner.isnot(None)).all())
