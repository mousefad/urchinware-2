import copy
import re
import os
import sys
import logging


log = logging.getLogger(os.path.basename(sys.argv[0]))


class GeTem:
    """Good enough templates.

    Expand special tags in template text given a "context" in the form a dictionary. Keys in the context dictionary
    are used as values, lists to iterate over, and varibales for expressions in conditionals.

    Value Tags <v:id> substitude the string value of context[id] into the result. printf-style format strings can be
    specified with <v:id:fmt>.

    Fixed Tags <f:id> replace id with some fixed text. id can take the following values: blank, newline, tab,
    backspace and delete.

    Iterator tags <i:id>...</i> expects id in the context dictionary to be a list of dictionaries. ... will be
    expanced one for each item in the list, using the item in the list as the context to expand ... with.

    Read file tags <r:id> searches for the filename id in all the search paths specified when the GeTem object was
    constructed. If found, the contents of the file are appened to the template and evaluation continues. Files
    included in this way can also include tags, including <r:id> tags, although it is not permitted for a file
    to include itself. Whitespace can be stripped from the end of the read file using <r:id:stripws>. Similarly
    EOL characters canbe stripped with <r:id:stripeol>.

    Conditional tags <c:expr>...<else>...</c> evaulate to the ... before or after the <else> depending on whenther
    expr evaluates to true or false.

    """

    NextTagRx = re.compile(
        r"^(.*?)(?<!\\)(<(v|f|i|r|c)(:([^:\s]+?)(:([^>]+?))?)?>)(.*)",
        re.MULTILINE | re.DOTALL,
    )
    NextIterationTagRx = re.compile(
        r"(.*?)(?<!\\)(</i>|<i(:([^\s]+?)(:(\S+?))?)?>)(.*)", re.MULTILINE | re.DOTALL
    )
    NextConditionTagRx = re.compile(
        r"(.*?)(?<!\\)(</c>|<c(:([^\s]+?)(:(\S+?))?)?>)(.*)", re.MULTILINE | re.DOTALL
    )
    FmtWidthRx = re.compile(r"%(-)?0?(\d+)")

    class DeleteChar(Exception):
        def __init__(self, count=1):
            self.count = count

    class BackspaceChar(Exception):
        def __init__(self, count=1):
            sef.count = count

    def __init__(self, text, paths=list(), encoding="utf8", errors="strict"):
        """Create a templata object.

        positional arguments:
        text: the template text, including tags.
        paths: a list of paths to search for files referenced by <r:filename> tags.
        encoding: string encoding for reading files.
        errors: string encoding error method.
        """
        if type(paths) is str:
            self.paths = [paths]
        else:
            assert type(paths) is list
            self.paths = paths
        self.text = text
        self.encoding = encoding
        self.errors = errors

    def __call__(
        self,
        data=dict(),
        text=None,
        missing="",
        it_count=0,
        it_last=False,
        read_files=set(),
    ):
        """Call a template with a dict of data to populate the template with.

        positional arguments:
        data: a dict of data with values to use with the template tags.
        text: template text. if not specied, the text used to construct the template is used.
        missing: what to put when there is no match for a value in the data.
        it_count: internal use
        it_last: internal use
        read_files: internal use
        """
        if text is None:
            text = copy.copy(self.text)
        result = ""
        while len(text) > 0:
            m = GeTem.NextTagRx.match(text)
            if not m:
                result += text
                break
            pre, alltag, tagtype, tagtail, id, allfmt, fmt, text = m.groups()
            result += pre
            if tagtype == "v":
                result += self.v_tag_expand(alltag, id, fmt, data, missing)
            elif tagtype == "i":
                iteration_template, text = self.split_iteration_segment(text)
                assert type(data[id]) is list
                last_it = len(data[id]) - 1
                for it_num, item in enumerate(data[id]):
                    iteration_data = copy.deepcopy(item)
                    assert type(iteration_data) is dict
                    for k, v in data.items():
                        if k != id and k not in iteration_data:
                            iteration_data[k] = v
                    result += self(
                        iteration_data,
                        iteration_template,
                        missing,
                        it_num,
                        it_num == last_it,
                    )
            elif tagtype == "c":
                match_template, else_template, text = self.split_conditional_segment(
                    text
                )
                m = re.match(r"(is_set|not_set)(\((.*)\))?$", fmt)
                assert m
                want = False
                if m.group(1) == "is_set":
                    want = id in data
                elif m.group(1) == "not_set":
                    want = id not in data
                else:
                    raise NotImplementedError(f"conditional type: {fmt}")
                if want:
                    result += self(
                        data, match_template, missing, it_count, it_last, read_files
                    )
                elif else_template != "":
                    result += self(
                        data, else_template, missing, it_count, it_last, read_files
                    )
            elif tagtype == "f":
                try:
                    result += self.f_tag_expand(
                        alltag, id, fmt, it_count, it_last, data
                    )
                except GeTem.BackspaceChar as e:
                    result = result[: (e.count * -1)]
                except Template.DeleteChar as e:
                    text = text[e.count :]
            elif tagtype == "r":
                try:
                    if id.startswith("@"):
                        indirect = id[1:]
                        assert (
                            indirect in data
                        ), f"indirect e tag argument: {indirect} not found in data"
                        id = data[indirect]
                    assert id not in read_files, "circular include"
                    read_files.add(id)
                    read_args = {"path": id}
                    if fmt is not None:
                        read_args[fmt] = True
                    result += self(
                        data, self.read(**read_args), missing, read_files=read_files
                    )
                    read_files.remove(id)
                except Exception as e:
                    log.warning(f"failed for tag {alltag} : {e!s}")
                    result += alltag
                    read_files.remove(id)
            else:
                log.warn(f"template_data_struct unknown tag {alltag}")
                result += alltag
        return result

    def read(self, path, stripws=False, stripeol=False):
        """read a file (to be found in paths specified in constructor) and return the contents.

        positional arguments:
        path: to be appended to each search path in turn until found
        stripws: strip whitespeace from the end of the result
        stripeol: string EOL characters from the end of the result
        """
        dirs = copy.copy(self.paths)
        dirs.append(os.curdir)
        for d in dirs:
            candidate_path = os.path.join(d, path)
            try:
                with open(
                    candidate_path, "r", encoding=self.encoding, errors=self.errors
                ) as f:
                    if stripws:
                        return f.read().rstrip("\n\r\t ")
                    elif stripeol:
                        return f.read().rstrip("\n\r")
                    else:
                        return f.read()
            except FileNotFoundError as e:
                pass
        raise FileNotFoundError(2, path)

    def v_tag_expand(self, alltag, id, fmt, data, missing):
        """Expand a value tag.

        positional arguments:
        alltag: the full tag text.
        id: the identifer the tag refers to in data.
        fmt: a format string to be used to format the value.
        data: a dict of items, which we expect to contain id.
        missing: what to use if id is not found in data.
        """
        value = None
        try:
            value = data[id]
            if fmt:
                result = fmt % value
            else:
                result = value
        except Exception as e:
            if "%r" in missing:
                missing = missing % alltag
            result = missing
        try:
            result = self.string_fmt(fmt) % result
        except:
            pass
        return result

    def string_fmt(self, fmt):
        try:
            m = GeTem.FmtWidthRx.match(fmt)
            if m:
                align = "" if m.group(1) is None else "-"
                return f"%{align}{m.group(2)}s"
        except:
            pass
        return "%s"

    def split_iteration_segment(self, template):
        segment = ""
        depth = 1
        while len(template) > 0:
            m = GeTem.NextIterationTagRx.match(template)
            if not m:
                raise RuntimeError("iteration tag not closed")
            tag = m.group(2)
            pre = m.group(1)
            template = m.group(7)
            segment += pre
            if tag == "</i>":
                if depth == 1:
                    break
                else:
                    depth -= 1
            else:
                depth += 1
            segment += tag
        return segment, template

    def split_conditional_segment(self, template):
        segment = ""
        else_segment = ""
        depth = 1
        while len(template) > 0:
            m = GeTem.NextConditionTagRx.match(template)
            if not m:
                raise RuntimeError("conditional tag not closed")
            tag = m.group(2)
            pre = m.group(1)
            template = m.group(7)
            segment += pre
            if tag == "</c>":
                if depth == 1:
                    break
                else:
                    depth -= 1
            else:
                depth += 1
            segment += tag
        m = re.match(r"(.*)(?<!\\)<else>(.*)", segment, re.DOTALL)
        if m:
            segment = m.group(1)
            else_segment = m.group(2)
        return segment, else_segment, template

    def f_tag_expand(self, alltag, id, fmt, it_count, it_last, data):
        result = ""
        if id == "blank":
            result = fmt % ""
        elif id in ("newline"):
            assert fmt is None
            result = "\n"
        elif id == "tab":
            assert fmt is None
            result = "\t"
        elif id in ("backspace"):
            count = 1 if fmt is None else int(fmt)
            raise GeTem.BackspaceChar(count)
        elif id in ("delete", "del"):
            count = 1 if fmt is None else int(fmt)
            raise GeTem.DeleteChar(count)
        else:
            m = re.match(r'^"([^"\s]+)"$', id)
            if m:
                result = fmt % m.group(1)
            else:
                raise RuntimeError(f"invalid format tag: {alltag}")
        return result


def main():
    from datetime import datetime

    data = {
        "org": "Church of the Sub-Genius.",
        "members": [
            {"n": 1, "name": "'Bob'", "dollars": 1000000, "much": True},
            {"n": 2, "name": "Stang", "dollars": 30},
            {"n": 3, "name": "Philo", "dollars": 30},
            {"n": 4, "name": "Dr. Hal", "dollars": 0},
        ],
    }

    tt = "Org: <v:org><i:members>\n#<v:n> is <v:name>, who has $<v:dollars> which is <c:much:is_set>a lot<else>not much</c></i>"
    t = GeTem(tt)
    print(t(data))

    print(
        GeTem("<r:1.t>")(
            {"subform": [{"value": 1}, {"value": 2}, {"bananas": 3}]}, missing="-"
        )
    )


if __name__ == '__main__':
    main()
