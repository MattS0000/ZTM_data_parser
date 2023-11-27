from collections import defaultdict
import networkx as nx


def read_id_len(line):
    line = line.split()
    return line[0].replace("*", ""), int(line[1])


def parse_section(section_id, section_length, nextline, verbose=False):
    section_dir = {}
    for i in range(section_length):
        section_line = nextline()
        if section_id == "TY" or section_id == "SM":
            section_line_data = section_line.split(maxsplit=1)
            section_dir[section_line_data[0]] = section_line_data[1].strip()
        elif section_id == "KA":
            section_line_data = section_line.split()
            section_dir[section_line_data[0]] = section_line_data[2:]
        elif section_id == "KD":
            subsection_id, subsection_length = read_id_len(section_line)
            subsection_dir = {}
            for j in range(subsection_length):
                temp_line = nextline()
                bus_num, tag = temp_line.split()
                subsection_dir[bus_num] = tag
            section_dir[subsection_id] = subsection_dir
        elif section_id == "ZA" or section_id == "ZP":
            # check if replacing ',' with ' ' isnt better
            temp_data = [
                s.strip() for s in section_line.replace(",", " ").split("  ") if s
            ]
            stop_id = temp_data[0]
            street, code, city = temp_data[1:]
            if code == "--":
                code = "XX"  # Warsaw is XX
            section_dir[stop_id] = [street, code, city]
            if section_id == "ZP":
                subsection_line = nextline()
                subsection_id, subsection_length = read_id_len(subsection_line)
                sub_dir = {}
                for j in range(subsection_length):
                    subsub_dir = {}
                    subsubsection_line = nextline()
                    subsub_data = [
                        s.strip()
                        for s in subsubsection_line.replace(",", " ").split("  ")
                        if s
                    ]
                    subsub_id, subsub_length, subsub_other = (
                        subsub_data[0],
                        int(subsub_data[1]),
                        subsub_data[2:],
                    )
                    for val, rep, k in zip(
                        ["Ul./Pl.", "Kier.", "Y", "X", "Pu"],
                        ["Ul./Pl.: ", "Kier.: ", "Y= ", "X= ", "Pu="],
                        [0, 1, 2, 3, 4],
                    ):
                        subsub_dir[val] = subsub_other[k].replace(rep, "")
                    for subsub_type in [
                        "dla wsiadających",
                        "dla wysiadających",
                        "krańcowy",
                        "na żądanie",
                        "stały",
                        "postojowy",
                    ]:
                        subsub_dir[subsub_type] = []
                    for k in range(subsub_length):
                        subsubsub_line = nextline().replace("L", "")
                        split = subsubsub_line.split("  ")
                        subsubsub_data = [
                            s.strip().replace("- ", "").replace(":", "")
                            for s in split
                            if s
                        ]
                        subsub_dir[subsubsub_data[1]] = subsubsub_data[2:]
                    sub_dir[subsub_id] = subsub_dir
                section_dir[stop_id].append(sub_dir)
                hash_sub_line = nextline()
        elif section_id == "LL":
            # Linia:   1  - LINIA TRAMWAJOWA
            line_id = section_line[3:13].split(":")[1].strip()  # 1
            line_type = section_line[17:]  # LINIA TRAMWAJOWA
            section_dir[line_id] = {
                "Line_type": line_type,
                "TR": {},
                "WK": [],
            }
            subsection_dir = section_dir[line_id]["TR"]
            subsection_tag, subsection_length = read_id_len(nextline())  # *TR 2
            for j in range(subsection_length):  # 2
                subsection_line = (
                    nextline().replace(",", " ").replace("--", "XX")
                )  # TO-ANN  ,  Rogaliñska,   --  ==>  Annopol, ...
                subsection_data = [
                    s.strip() for s in subsection_line.split("  ") if s
                ]  # ['TO-ANN', 'Rogalińska', 'XX', '==>', 'Annopol', 'XX', 'Kier. A', 'Poz. 0']
                subsection_dir[subsection_data[0]] = {
                    "start_stop": subsection_data[1],
                    "start_city": subsection_data[2],
                    "end_stop": subsection_data[4],
                    "end_city": subsection_data[5],
                    "direction": subsection_data[6],
                    "level": subsection_data[7],
                    "LW": [],
                    "RP": {},
                }
                LW_list = subsection_dir[subsection_data[0]]["LW"]
                RP_dir = subsection_dir[subsection_data[0]]["RP"]
                subsubsection_tag, subsubsection_len = read_id_len(
                    nextline()
                )  # *LW  29
                last_street = None
                custom_split_dic = lambda x: {
                    "street": x[:32].strip(),
                    "r": x[32].strip(),
                    "stop_id": x[34:40].strip(),
                    "stop_group": x[34:38].strip(),
                    "stop_group_id": x[38:40].strip(),
                    "stop_name": x[42:74].strip(),
                    "city": x[74:76].strip(),
                    "stop_on_demand": x[81:83].strip(),
                    "min_travel_time": x[86:88].strip(),
                    "max_travel_time": x[89:91].strip(),
                }
                for k in range(subsubsection_len):  # 29
                    subsub_line = nextline().replace(",", " ")[15:]
                    # split 'al."Solidarnosci",              r 500403  Zajezdnia Wola,                 -- 03  NŻ  | 7| 7|'
                    subsub_data = custom_split_dic(subsub_line)
                    if subsub_data["street"] != "":
                        last_street = subsub_data["street"]
                    subsub_data["street"] = last_street
                    LW_list.append(subsub_data)
                hash_sub_line = nextline()
                subsubsection2_tag, subsubsection2_len = read_id_len(
                    nextline()
                )  # *RP  25
                for k in range(subsubsection2_len):
                    # 500403  Zajezdnia Wola,                 --    Y= 52.235268     X= 20.974324     Pu=9
                    subsub_line = nextline().replace(",", " ").strip()
                    subsub_data = [s.strip() for s in subsub_line.split("  ") if s]
                    # ['500403', 'Zajezdnia Wola', '--', 'Y= 52.235268', 'X= 20.974324', 'Pu=9']
                    subsubsub_id, subsubsub_len = read_id_len(nextline())  # *TD 2
                    RP_dir[subsub_data[0]] = {
                        "stop_name": subsub_data[1],
                        "city": subsub_data[2],
                        "Y": subsub_data[3].replace("Y= ", ""),
                        "X": subsub_data[4].replace("X= ", ""),
                        "Pu": subsub_data[4].replace("Pu=", ""),
                        "TD": {},
                        "OP": [],
                    }
                    for l in range(subsubsub_len):
                        subsubsub_line = nextline().strip()  # SB  SOBOTA
                        subsubsub_data = [
                            subsubsub_line[:2],
                            subsubsub_line[4:51].replace(",", " ").strip(),
                            subsubsub_line[51:],
                        ]
                        RP_dir[subsub_data[0]]["TD"][subsubsub_data[0]] = {
                            "full_name": subsubsub_data[1],
                            "additional_info": subsubsub_data[2],
                            "WG": [],
                            "OD": [],
                        }
                        if not "NIE KURSUJE" in subsubsub_data[2]:
                            subsubsubsub_id, subsubsubsub_len = read_id_len(
                                nextline()
                            )  # *WG 17
                            for m in range(subsubsubsub_len):
                                subsubsubsub_line = nextline()  # G  2   5:  [32]^ [52]^
                                subsubsubsub_data = subsubsubsub_line.split()
                                hour = subsubsubsub_data[2]
                                subsubsubsub_full_data = [
                                    hour + i for i in subsubsubsub_data[3:]
                                ]
                                RP_dir[subsub_data[0]]["TD"][subsubsub_data[0]][
                                    "WG"
                                ].extend(subsubsubsub_full_data)
                            subsubsubsub_hash = nextline()
                            subsubsubsub_id, subsubsubsub_len = read_id_len(
                                nextline()
                            )  # *OD 53
                            custom_split_dic = lambda x: {
                                "departure_time": x[0],
                                "full_code": x[1],
                                "route_variant": x[2],
                                "date_type": x[3],
                                "first_stop_departure": x[4],
                            }
                            for m in range(subsubsubsub_len):
                                subsubsubsub_line = (
                                    nextline()
                                )  # 7.32  TD-1AN04/DS/07.31
                                subsubsubsub_data = subsubsubsub_line.split()
                                subsubsubsub_full_data = (
                                    subsubsubsub_data
                                    + subsubsubsub_data[1].replace("__", "").split("/")
                                )
                                RP_dir[subsub_data[0]]["TD"][subsubsub_data[0]][
                                    "OD"
                                ].append(custom_split_dic(subsubsubsub_full_data))
                            subsubsubsub_hash = nextline()
                    subsubsub_hash = nextline()  ##TD
                    subsubsub_id, subsubsub_len = read_id_len(nextline())  # *OP   4
                    for l in range(subsubsub_len):
                        subsubsub_line = nextline()[21:]
                        subsubsub_data = subsubsub_line.split("   ")
                        if len(subsubsub_data) == 1:
                            subsubsub_data.append("")
                        RP_dir[subsub_data[0]]["OP"].append(
                            (subsubsub_data[0], subsubsub_data[1])
                        )
                    subsubsub_hash = nextline()  ##OP
                subsub_hash = nextline()  ##RP
            sub_hash = nextline()  ##TR
            sub_id, sub_len = read_id_len(nextline())
            custom_split = lambda x: [
                x[:17],
                x[19:25],
                x[26:28],
                x[29:34].strip(),
                x[36:].replace(" ", ""),
            ]
            for j in range(sub_len):
                sub_line = nextline()[
                    9:
                ]  #         TD-1AN04/DS/07.31  108704 DS  8.05  P
                sub_data = custom_split(sub_line)
                sub_full_data = (
                    [sub_data[0]]
                    + sub_data[0].replace("__", "").split("/")
                    + sub_data[1:]
                )
                section_dir[line_id]["WK"].append(sub_full_data)
            sub_hash = nextline()
    return section_dir


def parse_file(path, verbose=False):
    sections = {}
    with open(path, encoding="cp1250") as f:
        nextline = lambda: f.readline().replace("\n", "")
        while f.readable():
            curr_line = nextline()
            if "*" in curr_line:
                section_id, section_length = read_id_len(curr_line)
                if verbose:
                    print(section_id, section_length)
                section_dir = parse_section(
                    section_id, section_length, nextline, verbose=verbose
                )
                sections[section_id] = section_dir
                hash_line = nextline()
                if verbose:
                    print(hash_line)
                if section_id == "LL":
                    break
            else:
                continue
        sections["SM"]["XX"] = "WARSZAWA"
    return sections


def get_connections(ztm_data):
    levels = defaultdict(nx.DiGraph)
    for line_nr, line_dict in ztm_data["LL"].items():
        line_type = line_dict["Line_type"]
        for route, route_dict in line_dict["TR"].items():
            last_non_empty = None
            for i in range(len(route_dict["LW"]) - 1):
                first_stop = route_dict["LW"][i]
                if first_stop["stop_id"] == "":
                    continue
                last_non_empty = first_stop
                second_stop = route_dict["LW"][i + 1]
                if second_stop["stop_id"] == "" and i + 2 < len(route_dict["LW"]):
                    second_stop = route_dict["LW"][i + 2]
                if second_stop["stop_id"] == "":
                    continue
                levels[line_type].add_edge(
                    first_stop["stop_id"], second_stop["stop_id"]
                )
    whole_network = nx.DiGraph()
    for g in levels.values():
        whole_network.add_edges_from(list(g.edges()))
    measures = list(levels.items()) + [("Whole Network", whole_network)]
    return measures
