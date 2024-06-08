# Build-in modules
import logging
import sys
import os

# PIP-installed modues
from singleton_decorator import singleton
from sqlalchemy import (
    create_engine,
    delete,
    ForeignKey,
    Column,
    String,
    Boolean,
    Integer,
    Float,
)
import sqlalchemy
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

log = logging.getLogger(os.path.basename(sys.argv[0]))

Base = declarative_base()


class Broker(Base):
    __tablename__ = "brokers"
    id = Column(String, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False, default=1883)
    keep_alive = Column(Integer, nullable=False, default=60)
    clean = Column(Boolean, nullable=False, default=True)
    client_id = Column(String, nullable=False, default="Dorcas")

    def __repr__(self):
        return f"Broker(id={self.id!r}, host={self.host!r}, port={self.port!r}, ...)"


class Effect(Base):
    __tablename__ = "effects"
    id = Column(String, primary_key=True)
    args = Column(String, nullable=False)

    def __repr__(self):
        return f"Effect(id={self.id!r}, args={self.args!r})"


class Voice(Base):
    __tablename__ = "voices"
    id = Column(String, primary_key=True)
    engine = Column(String, nullable=False)
    voice = Column(String, nullable=False)
    pitch = Column(Integer, nullable=False)
    amplitude = Column(Integer, nullable=False)
    speed = Column(Integer, nullable=False)
    gap = Column(Integer, nullable=False)
    effect_id = Column(String, ForeignKey("effects.id"))
    effect = relationship("Effect")

    def __repr__(self):
        return f"Voice(id={self.id!r}, voice={self.voice!r}, pitch={self.pitch!r}, amplitude={self.amplitude!r}, speed={self.speed!r}, gap={self.gap!r}, effect_id={self.effect_id!r})"


class Ignore(Base):
    __tablename__ = "ignores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_re = Column(String, nullable=False)
    message_re = Column(String, nullable=False)

    def __repr__(self):
        return f"Ignore(topic_re={self.topic_re!r}, message_re={self.message_re!r})"


class SpecialDay(Base):
    __tablename__ = "special_days"
    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=True)  # NULL means every year
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    story = Column(String, nullable=True)

    def __repr__(self):
        return f"SpecialDay(id={self.id!r}, year={self.year!r}, month={self.month!r}, day={self.day!r}, name={self.name!r})"


class Config(Base):
    __tablename__ = "configs"
    id = Column(String, primary_key=True)
    broker_id = Column(String, ForeignKey("brokers.id"))
    broker = relationship("Broker")
    voice_id = Column(String, ForeignKey("voices.id"))
    voice = relationship("Voice")
    time_interval = Column(Float, nullable=False)
    journal_interval = Column(Float, nullable=False)
    boredom_minimum = Column(Integer, nullable=False)
    boredom_amount = Column(Float, nullable=False)
    door_open_seconds = Column(Integer, nullable=False)
    mute_switch = Column(Boolean, nullable=False)

    def __repr__(self):
        return f"Config(id={self.id!r}, broker_id={self.broker_id!r}, voice_id={self.voice_id!r}, ...)"


class Greeting(Base):
    __tablename__ = "greetings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=False)
    member = Column(String, nullable=True, index=True)
    condition = Column(String, nullable=True)
    weight = Column(Integer, nullable=False, default=1)

    def __repr__(self):
        return f"Greeting(text={self.text!r}, member={self.member}, condition={self.condition!r}, weight={self.weight!r})"


# We'll have a separate table for Musings even though it's the same structure as Greetings...  because
# there will be a lot of greetings, which are less often evaluated. This way musings (which get evaluated
# very often), can be kept to a shorter list for efficiency's sake.
class Musing(Base):
    __tablename__ = "musings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=False)
    topic = Column(String, nullable=False, index=True)
    condition = Column(String, nullable=True)
    weight = Column(Integer, nullable=False, default=1)

    def __repr__(self):
        return f"Musing(text={self.text!r}, topic={self.topic!r}, condition={self.condition!r}, weight={self.weight!r})"


@singleton
class DB:
    def __init__(self, path, debug):
        self.path = path
        self.engine = create_engine(f"sqlite:///{self.path}", echo=debug)
        self.session = None
        if not os.path.exists(path):
            self.create_new_database()
        self.create_session()

    def create_new_database(self):
        log.info(f"database {self.path} does not exist - creating new database")
        Base.metadata.create_all(bind=self.engine)

    def create_session(self):
        if not self.session:
            self.session = sessionmaker(bind=self.engine)()

    def config(self, config_id):
        return self.session.query(Config).filter(Config.id == config_id).first()


if __name__ == "__main__":
    database_path = os.environ["DORCAS_DATABASE"]
    gnm = lambda x: "{http://www.gnumeric.org/v10.dtd}" + x
    office = lambda x: "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}" + x

    def do_pdb():
        DB(database_path, debug=True)
        breakpoint()

    def do_clean():
        print(f"Removing and re-creating {database_path}")
        if os.path.exists(database_path):
            os.remove(database_path)
        db = DB(database_path, debug=False)
        print(f"Created database with some basic entries.")

    def do_query():
        from sqlalchemy import or_, and_

        day = 19
        month = 4
        year = 2024
        print(
            DB(database_path, debug=False)
            .session.query(SpecialDay)
            .filter(
                and_(
                    SpecialDay.month == month,
                    SpecialDay.day == day,
                    or_(SpecialDay.year == None, SpecialDay.year == 2024),
                )
            )
            .first()
        )

    def load_configs(sheet):
        log.info("load_configs")
        load_generic(Config, sheet, [])

    def load_brokers(sheet):
        log.info("load_brokers")
        load_generic(Broker, sheet, [])

    def load_ignores(sheet):
        log.info("load_ignores")
        load_generic(Ignore, sheet, ["id"])

    def load_voices(sheet):
        log.info("load_voices")
        load_generic(Voice, sheet, [])

    def load_effects(sheet):
        log.info("load_effects")
        load_generic(Effect, sheet, [])

    def load_special_days(sheet):
        log.info("load_special_days")
        load_generic(SpecialDay, sheet, ["id"])

    def load_greetings(sheet):
        log.info("load_greetings")
        load_generic(Greeting, sheet, ["id"])

    def load_musings(sheet):
        log.info("load_musings")
        load_generic(Musing, sheet, ["id"])

    def load_generic(tclass, sheet, excludes):
        # excludes these auto fields
        sheet_name = sheet.find(gnm("Name")).text
        excludes.extend(["registry", "metadata"])
        typemap = {"Integer": int, "Float": float, "String": str, "Boolean": bool}
        field_names = [
            x
            for x in dir(tclass)
            if not x.startswith("_")
            and x not in excludes
            and type(getattr(tclass, x).expression)
            is sqlalchemy.sql.annotation.AnnotatedColumn
        ]
        field_types = {
            x: typemap[type(getattr(tclass, x).expression.type).__name__]
            for x in field_names
        }
        # Make a list of the sheet headings to column numbers, e.g. { "text": 0, "condition": 1, ...}
        cells = sheet.find(gnm("Cells")).findall(gnm("Cell"))
        sheet_columns = {x.text: n for n, x in enumerate(cells) if x.get("Row") == "0"}
        # Check we have all the desired fields in the sheet
        for field in field_types.keys():
            assert (
                field in sheet_columns
            ), f"Table class {tclass.__name__} expects field {field} - not found in sheet"

        row_count = max(
            [
                int(x.get("Row"))
                for x in cells
                if x.get("Col") == "1" and x.text is not None and len(x.text) > 0
            ]
        )
        try:
            DB().session.execute(delete(tclass))
            for row in range(1, row_count + 1):
                try:
                    row_data = [x.text for x in cells if x.get("Row") == str(row)]
                    row_dict = dict()
                    for field_name, field_type in field_types.items():
                        sheet_col = sheet_columns[field_name]
                        sheet_value = row_data[sheet_col]
                        try:
                            if sheet_value == "NULL" or len(sheet_value) == 0:
                                sheet_value = None
                            elif sheet_value == "TRUE":
                                sheet_value = True
                            elif sheet_value == "FALSE":
                                sheet_value = False
                            else:
                                sheet_value = field_type(sheet_value)
                        except:
                            sheet_value = None
                        row_dict[field_name] = sheet_value
                    item = tclass(**row_dict)
                    DB().session.add(item)
                except Exception as e:
                    log.error(f"SKIPPING row {row+1} in {sheet_name} : {e}")
            DB().session.commit()
        except Exception as e:
            log.exception(f"while adding from {sheet_name} entity")
            DB().session.rollback()

    def do_load():
        import coloredlogs
        import xml.etree.ElementTree as ET

        def usage(status):
            fh = sys.stdout if status == 0 else sys.stderr
            fh.write(f"Usage:\n\n  {sys.argv[0]} load file.xml [table [table ...]\n")
            sys.exit(status)

        if len(sys.argv) < 3:
            usage(1)
        if sys.argv[2] in ("-h", "--help"):
            usage(0)

        xml_path = sys.argv[2]
        tables = sys.argv[3:]
        known_tables = (
            "configs",
            "brokers",
            "ignores",
            "voices",
            "effects",
            "special_days",
            "greetings",
            "musings",
        )
        if len(tables) == 0:
            tables = known_tables
        coloredlogs.install(level=logging.DEBUG)
        DB(database_path, debug=False)
        mute_switch_states = {x.id : x.mute_switch for x in DB().session.query(Config).all()}
        for what in tables:
            assert (
                what in known_tables
            ), f"table must be one of: {', '.join(known_tables)}"
        tree = ET.parse(xml_path)
        root = tree.getroot()
        log.debug(f"got XML root: {root}")
        sheets = root.find(gnm("Sheets"))

        def get_sheet(name):
            return [
                x
                for x in sheets.findall(gnm("Sheet"))
                if x.find(gnm("Name")).text == name
            ][0]

        for table in tables:
            sheet = get_sheet(table)
            fn = getattr(sys.modules["__main__"], f"load_{table}")
            fn(sheet)

        # restore mute switch states
        for id, mute in mute_switch_states.items():
            DB().config(id).mute_switch = mute
        DB().session.commit()

    commands = dict(
        [
            (x[3:], getattr(sys.modules[__name__], x))
            for x in dir(sys.modules[__name__])
            if x.startswith("do_")
        ]
    )

    def usage(status):
        fh = sys.stderr if status != 0 else sts.stdout
        cmds = "|".join(commands.keys())
        fh.write(f"Usage:\n\n{os.path.basename(sys.argv[0])} cmd\n\ncmds: {cmds}\n")
        sys.exit(status)

    if len(sys.argv) < 2:
        usage(1)
    if sys.argv[1] not in commands:
        usage(1)

    commands[sys.argv[1]]()
