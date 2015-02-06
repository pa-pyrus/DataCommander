#!/usr/bin/python
# vim:fileencoding=utf-8:ts=8:et:sw=4:sts=4:tw=79

"""
models.py: Model definitions for the Commander suite of services.

Copyright (c) 2015 Pyrus <pyrus at coffee dash break dot at>
See the file LICENSE for copying permission.
"""

from .common import Base

from sqlalchemy import Column, Table
from sqlalchemy import DateTime, Enum, Float, ForeignKey
from sqlalchemy import Integer, SmallInteger, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

import trueskill


game_player_table = Table("game_player", Base.metadata,
                          Column("gid", Integer,
                                 ForeignKey("game.gid", ondelete="CASCADE"),
                                 primary_key=True, index=True),
                          Column("pid", Integer,
                                 ForeignKey("player.pid", ondelete="CASCADE"),
                                 primary_key=True, index=True))


class Player(Base):
    __tablename__ = "player"

    pid = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String, nullable=False)
    _ts_mu = Column(Float, nullable=False)
    _ts_sigma = Column(Float, nullable=False)
    rating = Column(Float, nullable=False)
    updated = Column(DateTime, nullable=False)
    games = relationship("Game",
                         secondary=game_player_table,
                         back_populates="players")

    @hybrid_property
    def skill(self):
        return trueskill.Rating(self._ts_mu, self._ts_sigma)

    @skill.setter
    def skill(self, new_skill):
        try:
            mu, sigma = new_skill.mu, new_skill.sigma
            rating = trueskill.expose(new_skill)
        except AttributeError:
            # swallow the exception but don't modify values
            pass
        else:
            self._ts_mu, self._ts_sigma = mu, sigma
            self.rating = rating

    @property
    def wdl(self):
        w, d, l = 0, 0, 0
        w = sum(1 for g in self.games if g.wid == self.pid)
        d = sum(1 for g in self.games if g.wid is None)
        l = len(self.games) - (w + d)

        return w, d, l

    def __init__(self, pid, name, skill, updated):
        self.pid = pid
        self.name = name
        self._ts_mu = skill.mu
        self._ts_sigma = skill.sigma
        self.rating = trueskill.expose(skill)
        self.updated = updated

    def __repr__(self):
        return ("<Player(ID={0}, Rating={1}, Last Game={2})>".format(
            self.pid, self.rating, self.updated.isoformat(" ")))


class Game(Base):
    __tablename__ = "game"

    gid = Column(Integer, primary_key=True, autoincrement=False)
    wid = Column(Integer,
                 ForeignKey("player.pid", ondelete="CASCADE"),
                 nullable=True)
    winner = relationship("Player", uselist=False)

    players = relationship("Player",
                           secondary=game_player_table,
                           back_populates="games")

    def __init__(self, gid, winner, *players):
        if winner:
            assert winner in players
        assert len(set(players)) >= 2

        self.gid = gid
        self.winner = winner
        self.players = list(set(players))

    def __repr__(self):
        return ("<Game(ID={0}, "
                "Winner={1}, "
                "NofPlayers={2})>"
                .format(self.gid,
                        self.wid or "Draw",
                        len(self.players)))


class Patch(Base):
    __tablename__ = "patch"

    name = Column(String, primary_key=True)
    build = Column(String, nullable=False)
    description = Column(String, nullable=False)
    updated = Column(DateTime, nullable=False)

    def __init__(self, name, build, description, updated):
        self.name = name
        self.build = build
        self.description = description
        self.updated = updated

    def __repr__(self):
        return ("<Patch(Name={0}, Build={1}, Updated={2})>".format(
            self.name, self.build,
            self.updated.replace(second=0, microsecond=0).isoformat()))


class Tournament(Base):
    __tablename__ = "tournament"

    tid = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    winner = Column(String, nullable=True)
    mode = Column(String, nullable=False)
    url = Column(String, nullable=False)

    path = Column(String, nullable=False, unique=True, index=True)
    md5_hash = Column(String(32), nullable=False)

    def __init__(self, title, date, winner, mode, url, path, md5_hash):
        self.title = title
        self.date = date
        self.winner = winner
        self.mode = mode
        self.url = url

        self.path = path
        self.md5_hash = md5_hash

    def __repr__(self):
        return ("<Tournament(Title={0}, Date={1}, Winner={2})".format(
            self.title,
            self.date.replace(second=0, microsecond=0).isoformat(),
            self.winner))


class UberAccount(Base):
    __tablename__ = "uberaccount"

    uname = Column(String, primary_key=True)
    dname = Column(String, nullable=True)
    uid = Column(String, unique=True, nullable=False, index=True)
    pid = Column(Integer, nullable=True, index=True)

    def __init__(self, uber_name, uber_id, display_name, pastats_id):
        self.uname = uber_name
        self.dname = display_name
        self.uid = uber_id
        self.pid = pastats_id

    def __repr__(self):
        return ("<UberAccount(UberName={0}, UberId={1})>".format(
            self.uname, self.uid))


class LeaderBoardEntry(Base):
    __tablename__ = "leaderboard"

    league = Column(Enum("Uber", "Platinum", "Gold", "Silver", "Bronze",
                         name="league_enum"),
                    primary_key=True)
    rank = Column(SmallInteger, nullable=False, primary_key=True)
    uid = Column(String, ForeignKey("uberaccount.uid"), nullable=False)
    last = Column(DateTime, nullable=False)

    def __init__(self, league, rank, uid, last):
        self.league = league
        self.rank = rank
        self.uid = uid
        self.last = last

    def __repr__(self):
        return ("<LeaderBoardEntry(League={0}, Rank={1}, UberId={2})".format(
            self.league, self.rank, self.uid))
