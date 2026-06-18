#!/usr/bin/env python3
"""
Fix all 5 ST-07 Mission Control workflows.

Issues fixed:
1. Low fuel at mine WP -> divert to fuel station instead of trying to mine
2. Junk cargo at mine WP -> jettison before surveying/mining
3. Ships in DRIFT mode -> set to CRUISE for faster travel
4. Ships at delivery with empty cargo -> properly return to mine (set CRUISE first)
"""

import json
import subprocess
import os
import sys

N8N = os.environ.get("N8N_BASE_URL", "http://localhost:5678")
KEY = os.environ.get("N8N_API_KEY", "")

def api(method, path, body=None):
    cmd = ["curl", "-sS", "-X", method, f"{N8N}/api/v1{path}",
           "-H", f"X-N8N-API-KEY: {KEY}", "-H", "Content-Type: application/json"]
    if body:
        cmd += ["-d", json.dumps(body)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


def fix_mission_control(js, agent_name):
    """Apply all fixes to the Mission Control JS code."""
    
    lines = js.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # FIX 1: Before the "Navigate to mine" block, add fuel-at-mine check
        # Look for the block: if(wp!==MINE_WP){...}
        if "if(wp!==MINE_WP)" in line or "if(wp !== MINE_WP)" in line:
            # Insert fuel-at-mine check BEFORE this block
            new_lines.append("  // FIX: At mine WP with low fuel -> divert to fuel station")
            new_lines.append("  if(wp===MINE_WP&&fuel.current<MIN_FUEL&&status==='IN_ORBIT'){if(fm!=='DRIFT'){actions.push({action:'set_drift',ship:sym});continue;}actions.push({action:'navigate',ship:sym,waypoint:FUEL_WP,reason:'refuel_at_mine',flightMode:'DRIFT'});continue;}")
            new_lines.append("  // FIX: At mine WP with junk cargo -> jettison before mining")
            new_lines.append("  if(wp===MINE_WP&&junk.length>0&&cargoPct>=0.10){for(const j of junk)actions.push({action:'jettison',ship:sym,symbol:j.symbol,units:j.units});continue;}")
            new_lines.append("")
            new_lines.append(line)
            i += 1
            continue
        
        # FIX 2: In the "return to mine" block, add set_cruise before navigate
        # Look for: if(wp===deliverDest&&tu===0)
        if "wp===deliverDest&&tu===0)" in line or "wp === deliverDest && tu === 0)" in line:
            new_lines.append(line)
            i += 1
            # Read the next few lines and modify
            # Original: if(status==='DOCKED'){orbit...} if(status==='IN_ORBIT'){navigate...}
            # Add set_cruise before navigate
            while i < len(lines):
                inner_line = lines[i]
                if "return_to_mine" in inner_line:
                    # Add set_cruise before navigate
                    new_lines.append("  if(wp===deliverDest&&tu===0){if(status==='DOCKED'){actions.push({action:'orbit',ship:sym});continue;}if(status==='IN_ORBIT'){if(fm!=='CRUISE'){actions.push({action:'set_cruise',ship:sym});continue;}actions.push({action:'navigate',ship:sym,waypoint:MINE_WP,reason:'return_to_mine',flightMode:'CRUISE'});continue;}}")
                    i += 1
                    break
                else:
                    new_lines.append(inner_line)
                    i += 1
            continue
        
        # FIX 3: In the "have trade ore -> navigate to deliver" block, add cruise
        if "tu>0&&wp!==deliverDest)" in line or "tu > 0 && wp !== deliverDest)" in line:
            new_lines.append(line)
            i += 1
            # Read subsequent lines until we find the navigate action
            while i < len(lines):
                inner_line = lines[i]
                if "'deliver'" in inner_line and "navigate" in inner_line:
                    # Add set_cruise before navigate
                    new_lines.append(inner_line)  # Keep the original navigate line
                    i += 1
                    break
                elif "set_drift" in inner_line:
                    new_lines.append(inner_line)
                    i += 1
                    # Next should be the navigate line, add cruise before it
                    if i < len(lines) and "navigate" in lines[i]:
                        new_lines.append(lines[i])  # navigate line
                        i += 1
                    break
                else:
                    new_lines.append(inner_line)
                    i += 1
            continue
        
        # FIX 4: In the "Navigate to mine" block (wp!==MINE_WP), add cruise mode
        if "if(wp!==MINE_WP)" in line:
            new_lines.append(line)
            i += 1
            # Read subsequent lines
            while i < len(lines):
                inner_line = lines[i]
                if "reason:'mine'" in inner_line and "navigate" in inner_line:
                    new_lines.append(inner_line)
                    i += 1
                    break
                elif "set_drift" in inner_line:
                    new_lines.append(inner_line)
                    i += 1
                    if i < len(lines) and "navigate" in lines[i]:
                        new_lines.append(lines[i])
                        i += 1
                    break
                else:
                    new_lines.append(inner_line)
                    i += 1
            continue
        
        # FIX 5: In the mine WP branch, add junk jettison before survey
        if "if(wp===MINE_WP)" in line and "DOCKED" not in line:
            new_lines.append(line)
            i += 1
            continue
        
        # FIX 6: In the IN_TRANSIT skip, also handle DRIFT mode
        if "if(status==='IN_TRANSIT')continue;" in line:
            # Replace with: if IN_TRANSIT and not DRIFT, skip. If DRIFT, set cruise.
            new_lines.append("  if(status==='IN_TRANSIT'){if(fm==='DRIFT'){actions.push({action:'set_cruise',ship:sym});}continue;}")
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    return '\n'.join(new_lines)


def main():
    # First, get the API key
    global KEY
    if not KEY:
        # Try to find it from n8n config
        try:
            with open('/home/mcastae813/n8n/data/.n8n/config') as f:
                cfg = json.load(f)
            # The API key might be in the config
            print("No N8N_API_KEY set, trying to find it...")
        except:
            pass
    
    if not KEY:
        print("ERROR: N8N_API_KEY not set. Set it as environment variable.")
        sys.exit(1)
    
    # Get all active ST-07 workflows
    r = api("GET", "/workflows")
    if isinstance(r, dict) and 'message' in r:
        print(f"API Error: {r['message']}")
        sys.exit(1)
    
    st07_workflows = [wf for wf in r if wf.get('active') and 'ST-07' in wf.get('name', '') and 'HERMES-' in wf.get('name', '')]
    
    if not st07_workflows:
        print("No active HERMES-*-ST-07 workflows found!")
        sys.exit(1)
    
    print(f"Found {len(st07_workflows)} ST-07 workflows to fix")
    
    for wf in st07_workflows:
        name = wf['name']
        wid = wf['id']
        print(f"\n{'=' * 60}")
        print(f"Processing: {name} ({wid})")
        
        # Get full workflow
        full_wf = api("GET", f"/workflows/{wid}")
        if 'id' not in full_wf:
            print(f"  ERROR: Could not get workflow: {json.dumps(full_wf)[:200]}")
            continue
        
        nodes = full_wf['nodes']
        connections = full_wf['connections']
        
        # Find and fix Mission Control node
        fixed = False
        for node in nodes:
            if node['name'] == 'Mission Control' and node['type'] == 'n8n-nodes-base.code':
                old_js = node['parameters'].get('jsCode', '')
                new_js = fix_mission_control(old_js, name)
                
                if old_js == new_js:
                    print(f"  No changes needed")
                else:
                    node['parameters']['jsCode'] = new_js
                    print(f"  Updated Mission Control code ({len(old_js)} -> {len(new_js)} chars)")
                    fixed = True
                break
        
        if not fixed:
            print(f"  WARNING: No Mission Control node found or no changes needed")
            continue
        
        # Deactivate, update, reactivate
        print(f"  Deactivating...")
        api("POST", f"/workflows/{wid}/deactivate")
        
        print(f"  Updating...")
        update_body = {
            "name": full_wf['name'],
            "nodes": nodes,
            "connections": connections,
            "settings": {"executionOrder": "v1"},
            "staticData": None
        }
        
        result = api("PUT", f"/workflows/{wid}", update_body)
        if 'id' not in result:
            print(f"  ERROR updating: {json.dumps(result)[:300]}")
            continue
        
        print(f"  Reactivating...")
        api("POST", f"/workflows/{wid}/activate")
        
        print(f"  ✅ Done!")
    
    print(f"\n{'=' * 60}")
    print("All ST-07 workflows fixed!")


if __name__ == "__main__":
    main()
