"""
tree_renderer.py — Generates an interactive visual node-tree as HTML.
eBay IAC (root) -> Teams -> Members -> Artifacts
Real branches with SVG connector lines, expandable nodes.
"""

import json as _json
from data_manager import ARTIFACT_TYPES

TEAM_COLORS = [
    "#0064D2", "#E53238", "#86B817", "#F5AF02",
    "#6366f1", "#0891b2", "#c026d3", "#059669",
    "#dc2626", "#d97706",
]


def generate_tree_html(data, height=700):
    """Build full interactive tree HTML from vault data."""

    tree_json = _build_tree_json(data)

    html = """
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        .tree-canvas {
            width: 100%;
            height: """ + str(height) + """px;
            overflow: auto;
            position: relative;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f9fafb;
            border-radius: 10px;
            border: 1px solid #e5e7eb;
        }
        .tree-inner {
            position: relative;
            min-width: 100%;
            min-height: 100%;
            padding: 40px 30px 60px;
        }
        .node {
            position: absolute;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.18s ease, box-shadow 0.18s ease;
            user-select: none;
            z-index: 2;
        }
        .node:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        }
        .node-root {
            background: #1a1f2e;
            color: #fff;
            padding: 14px 28px;
            border-radius: 12px;
            text-align: center;
            min-width: 180px;
        }
        .node-root .n-title { font-size: 17px; font-weight: 700; letter-spacing: -0.2px; }
        .node-root .n-sub { font-size: 10px; opacity: 0.6; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 2px; }
        .node-root .ebay-bar { height: 3px; border-radius: 2px; background: linear-gradient(90deg, #E53238, #0064D2, #F5AF02, #86B817); margin-top: 8px; }
        .node-team {
            background: #fff;
            border: 2px solid #e5e7eb;
            padding: 10px 18px;
            text-align: center;
            min-width: 130px;
        }
        .node-team .n-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; vertical-align: middle; }
        .node-team .n-title { font-size: 13px; font-weight: 600; color: #1a1d23; display: inline; vertical-align: middle; }
        .node-team .n-count { font-size: 10px; color: #8b919e; margin-top: 3px; }
        .node-member {
            background: #fff;
            border: 1.5px solid #e5e7eb;
            padding: 8px 14px;
            text-align: center;
            min-width: 110px;
        }
        .node-member .n-avatar {
            width: 28px; height: 28px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 600; margin: 0 auto 4px;
        }
        .node-member .n-title { font-size: 12px; font-weight: 500; color: #1a1d23; }
        .node-member .n-count { font-size: 10px; color: #8b919e; margin-top: 1px; }
        .node-artifact {
            background: #fff;
            border: 1.5px solid #eef0f3;
            padding: 6px 12px;
            display: flex; align-items: center; gap: 6px;
            min-width: 90px; max-width: 200px;
        }
        .node-artifact .n-icon { font-size: 14px; }
        .node-artifact .n-title {
            font-size: 11px; font-weight: 500; color: #3d424d;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .node-artifact .n-badge {
            font-size: 9px; font-weight: 600; padding: 1px 5px; border-radius: 3px;
            text-transform: uppercase; letter-spacing: 0.3px; white-space: nowrap;
        }
        .tree-lines {
            position: absolute; top: 0; left: 0;
            pointer-events: none; z-index: 1;
        }
        .tree-lines path { fill: none; stroke-width: 1.5; stroke-linecap: round; }
        .empty-tree {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            height: 100%; color: #8b919e; text-align: center; padding: 60px;
        }
        .empty-tree .et-icon { font-size: 48px; opacity: 0.3; margin-bottom: 16px; }
        .empty-tree .et-text { font-size: 14px; max-width: 300px; line-height: 1.6; }
        .tree-tooltip {
            position: absolute; background: #1a1f2e; color: #fff;
            padding: 8px 14px; border-radius: 8px; font-size: 11px; line-height: 1.5;
            max-width: 250px; z-index: 100; pointer-events: none;
            opacity: 0; transition: opacity 0.15s;
        }
        .tree-tooltip.visible { opacity: 1; }
    </style>

    <div class="tree-canvas" id="treeCanvas">
        <div class="tree-inner" id="treeInner">
            <svg class="tree-lines" id="treeLines"></svg>
            <div id="treeNodes"></div>
            <div class="tree-tooltip" id="tooltip"></div>
        </div>
    </div>

    <script>
    var TREE_DATA = """ + tree_json + """;
    var TEAM_COLORS = """ + _json.dumps(TEAM_COLORS) + """;

    var NC = {
        rootW: 200, rootH: 58,
        teamW: 150, teamH: 52,
        memberW: 130, memberH: 60,
        artifactW: 180, artifactH: 32,
        levelGap: 70,
        siblingGap: 16
    };

    function layout() {
        var canvas = document.getElementById('treeCanvas');
        var inner = document.getElementById('treeInner');
        var nodesEl = document.getElementById('treeNodes');
        var linesEl = document.getElementById('treeLines');
        var tooltip = document.getElementById('tooltip');

        nodesEl.innerHTML = '';

        var teams = TREE_DATA.teams || {};
        var teamNames = Object.keys(teams);

        if (teamNames.length === 0) {
            nodesEl.innerHTML = '<div class="empty-tree"><div class="et-icon">&#127793;</div><div class="et-text">No teams yet.<br>Use the sidebar to add your first team,<br>then watch the tree grow.</div></div>';
            linesEl.innerHTML = '';
            inner.style.width = '100%';
            inner.style.height = '100%';
            return;
        }

        var nodes = [];
        var edges = [];

        function measureTeam(tName) {
            var members = Object.keys(teams[tName].members || {});
            if (members.length === 0) return NC.teamW;
            var total = 0;
            for (var mi = 0; mi < members.length; mi++) {
                var mName = members[mi];
                var arts = (teams[tName].members[mName] || {}).artifacts || [];
                var artW = arts.length > 0
                    ? arts.length * (NC.artifactW + NC.siblingGap) - NC.siblingGap
                    : NC.memberW;
                var mw = Math.max(NC.memberW, artW);
                total += mw + (mi > 0 ? NC.siblingGap * 2 : 0);
            }
            return Math.max(NC.teamW, total);
        }

        var totalW = 0;
        var teamWidths = {};
        for (var i = 0; i < teamNames.length; i++) {
            var w = measureTeam(teamNames[i]);
            teamWidths[teamNames[i]] = w;
            totalW += w + (i > 0 ? NC.siblingGap * 3 : 0);
        }

        var padX = 40;
        var padY = 40;
        var canvasW = Math.max(totalW + padX * 2, canvas.clientWidth);

        var rootX = canvasW / 2 - NC.rootW / 2;
        var rootY = padY;
        nodes.push({ id: 'root', type: 'root', x: rootX, y: rootY, w: NC.rootW, h: NC.rootH,
            label: TREE_DATA.organization || 'eBay IAC', sub: 'Artifact Vault' });

        var teamStartX = canvasW / 2 - totalW / 2;
        var teamY = rootY + NC.rootH + NC.levelGap;

        for (var ti = 0; ti < teamNames.length; ti++) {
            var tName = teamNames[ti];
            var tw = teamWidths[tName];
            var tx = teamStartX + tw / 2 - NC.teamW / 2;
            var color = TEAM_COLORS[ti % TEAM_COLORS.length];
            var mems = Object.keys(teams[tName].members || {});
            var aTotal = 0;
            for (var mm = 0; mm < mems.length; mm++) {
                aTotal += ((teams[tName].members[mems[mm]] || {}).artifacts || []).length;
            }

            nodes.push({ id: 'team_' + ti, type: 'team', x: tx, y: teamY, w: NC.teamW, h: NC.teamH,
                label: tName, color: color, count: mems.length + ' members, ' + aTotal + ' artifacts' });
            edges.push({ from: 'root', to: 'team_' + ti, color: color });

            if (mems.length > 0) {
                var memberY = teamY + NC.teamH + NC.levelGap;
                var memXCursor = teamStartX;

                for (var mi = 0; mi < mems.length; mi++) {
                    var mName = mems[mi];
                    var arts = (teams[tName].members[mName] || {}).artifacts || [];
                    var artBlockW = arts.length > 0
                        ? arts.length * (NC.artifactW + NC.siblingGap) - NC.siblingGap
                        : NC.memberW;
                    var memBlockW = Math.max(NC.memberW, artBlockW);
                    var mx = memXCursor + memBlockW / 2 - NC.memberW / 2;

                    var parts = mName.split(' ');
                    var initials = '';
                    for (var p = 0; p < parts.length && p < 2; p++) {
                        initials += parts[p][0];
                    }
                    initials = initials.toUpperCase();

                    nodes.push({ id: 'mem_' + ti + '_' + mi, type: 'member', x: mx, y: memberY,
                        w: NC.memberW, h: NC.memberH,
                        label: mName, initials: initials, color: color,
                        count: arts.length + ' artifact' + (arts.length !== 1 ? 's' : '') });
                    edges.push({ from: 'team_' + ti, to: 'mem_' + ti + '_' + mi, color: color });

                    if (arts.length > 0) {
                        var artY = memberY + NC.memberH + NC.levelGap * 0.8;
                        var artXCursor = memXCursor + memBlockW / 2 - artBlockW / 2;

                        for (var ai = 0; ai < arts.length; ai++) {
                            var art = arts[ai];
                            var aColor = art._color || '#6B7280';
                            nodes.push({ id: 'art_' + ti + '_' + mi + '_' + ai, type: 'artifact',
                                x: artXCursor, y: artY,
                                w: NC.artifactW, h: NC.artifactH,
                                label: art.name || 'Untitled',
                                icon: art._icon || '&#128206;',
                                badge: art._label || 'File',
                                badgeColor: aColor,
                                url: art.url || '',
                                tooltip: (art.notes || '') + (art.url ? '\\n' + art.url : '')
                            });
                            edges.push({ from: 'mem_' + ti + '_' + mi, to: 'art_' + ti + '_' + mi + '_' + ai, color: color + '60' });
                            artXCursor += NC.artifactW + NC.siblingGap;
                        }
                    }
                    memXCursor += memBlockW + NC.siblingGap * 2;
                }
            }
            teamStartX += tw + NC.siblingGap * 3;
        }

        var maxX = 0, maxY = 0;
        for (var n = 0; n < nodes.length; n++) {
            maxX = Math.max(maxX, nodes[n].x + nodes[n].w + padX);
            maxY = Math.max(maxY, nodes[n].y + nodes[n].h + padY + 30);
        }
        inner.style.width = maxX + 'px';
        inner.style.height = maxY + 'px';

        var nodeMap = {};
        for (var n = 0; n < nodes.length; n++) { nodeMap[nodes[n].id] = nodes[n]; }

        var pathsHTML = '';
        for (var e = 0; e < edges.length; e++) {
            var from = nodeMap[edges[e].from];
            var to = nodeMap[edges[e].to];
            if (!from || !to) continue;
            var x1 = from.x + from.w / 2;
            var y1 = from.y + from.h;
            var x2 = to.x + to.w / 2;
            var y2 = to.y;
            var midY = (y1 + y2) / 2;
            pathsHTML += '<path d="M' + x1 + ',' + y1 + ' C' + x1 + ',' + midY + ' ' + x2 + ',' + midY + ' ' + x2 + ',' + y2 + '" stroke="' + edges[e].color + '" />';
        }
        linesEl.setAttribute('width', maxX);
        linesEl.setAttribute('height', maxY);
        linesEl.innerHTML = pathsHTML;

        var nodesHTML = '';
        for (var n = 0; n < nodes.length; n++) {
            var nd = nodes[n];
            var style = 'left:' + nd.x + 'px;top:' + nd.y + 'px;width:' + nd.w + 'px;height:' + nd.h + 'px;';
            if (nd.type === 'root') {
                nodesHTML += '<div class="node node-root" style="' + style + '">'
                    + '<div class="n-title"><span style="color:#E53238">e</span><span style="color:#0064D2">B</span><span style="color:#F5AF02">a</span><span style="color:#86B817">y</span> IAC</div>'
                    + '<div class="n-sub">' + nd.sub + '</div>'
                    + '<div class="ebay-bar"></div></div>';
            } else if (nd.type === 'team') {
                nodesHTML += '<div class="node node-team" style="' + style + 'border-color:' + nd.color + '40;">'
                    + '<div><span class="n-dot" style="background:' + nd.color + ';"></span><span class="n-title">' + nd.label + '</span></div>'
                    + '<div class="n-count">' + nd.count + '</div></div>';
            } else if (nd.type === 'member') {
                nodesHTML += '<div class="node node-member" style="' + style + '">'
                    + '<div class="n-avatar" style="background:' + nd.color + '18;color:' + nd.color + ';">' + nd.initials + '</div>'
                    + '<div class="n-title">' + nd.label + '</div>'
                    + '<div class="n-count">' + nd.count + '</div></div>';
            } else if (nd.type === 'artifact') {
                var tt = nd.tooltip ? ' data-tip="' + nd.tooltip.replace(/"/g, '&quot;') + '"' : '';
                var click = nd.url ? ' onclick="window.open(\\'' + nd.url.replace(/'/g, "\\\\'") + '\\', \\'_blank\\')"' : '';
                nodesHTML += '<div class="node node-artifact" style="' + style + '"' + tt + click + '>'
                    + '<span class="n-icon">' + nd.icon + '</span>'
                    + '<span class="n-title">' + nd.label + '</span>'
                    + '<span class="n-badge" style="background:' + nd.badgeColor + '15;color:' + nd.badgeColor + ';">' + nd.badge + '</span></div>';
            }
        }
        nodesEl.innerHTML = nodesHTML;

        var tipEls = document.querySelectorAll('[data-tip]');
        for (var t = 0; t < tipEls.length; t++) {
            tipEls[t].addEventListener('mouseenter', function(e) {
                var tip = e.target.closest('[data-tip]').getAttribute('data-tip').trim();
                if (!tip) return;
                tooltip.textContent = tip;
                tooltip.style.left = (e.target.offsetLeft) + 'px';
                tooltip.style.top = (e.target.offsetTop - 36) + 'px';
                tooltip.classList.add('visible');
            });
            tipEls[t].addEventListener('mouseleave', function() { tooltip.classList.remove('visible'); });
        }
    }

    layout();
    </script>
    """
    return html


def _build_tree_json(data):
    out = {
        "organization": data.get("organization", "eBay IAC"),
        "teams": {}
    }
    for t_name, t_data in data.get("teams", {}).items():
        team_out = {"members": {}}
        for m_name, m_data in t_data.get("members", {}).items():
            arts_out = []
            for a in m_data.get("artifacts", []):
                atype = a.get("type", "other_file")
                info = ARTIFACT_TYPES.get(atype, ARTIFACT_TYPES["other_file"])
                arts_out.append({
                    "name": a.get("name", "Untitled"),
                    "type": atype,
                    "url": a.get("url", ""),
                    "notes": a.get("notes", ""),
                    "_icon": info["icon"],
                    "_label": info["label"],
                    "_color": info["color"],
                })
            team_out["members"][m_name] = {"artifacts": arts_out}
        out["teams"][t_name] = team_out
    return _json.dumps(out)
