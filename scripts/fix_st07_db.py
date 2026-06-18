#!/usr/bin/env python3
"""
Fix all 5 ST-07 Mission Control workflows by directly updating the n8n database.
Handles:
1. Low fuel at mine WP -> divert to fuel station
2. Junk cargo at mine WP -> jettison before mining
3. Ships in DRIFT mode -> set to CRUISE
4. Ships at delivery with empty cargo -> return to mine with CRUISE
"""

import sqlite3
import json
import shutil
import os
from datetime import datetime

DB_PATH = '/home/mcastae813/n8n/data/.n8n/database.sqlite'
BACKUP_PATH = f'/home/mcastae813/n8n/data/.n8n/database.sqlite.bak.{datetime.now().strftime("%Y%m%d_%H%M%S")}'

def fix_mission_control(js):
    """Apply all fixes to the Mission Control JS code."""
    
    # We'll do targeted string replacements
    
    # FIX 1: Add fuel-at-mine and junk-at-mine checks BEFORE the "Navigate to mine" block
    # Find: if(wp!==MINE_WP){
    # Insert fuel check and junk check before it
    
    old_navigate_mine = "  // Navigate to mine\n  if(wp!==MINE_WP)"
    new_navigate_mine = """  // FIX: At mine WP with low fuel -> divert to fuel station
  if(wp===MINE_WP&&fuel.current<MIN_FUEL&&status==='IN_ORBIT'){if(fm!=='DRIFT'){actions.push({action:'set_drift',ship:sym});continue;}actions.push({action:'navigate',ship:sym,waypoint:FUEL_WP,reason:'low_fuel_at_mine',flightMode:'DRIFT'});continue;}
  // FIX: At mine WP with junk cargo -> jettison before mining
  if(wp===MINE_WP&&junk.length>0&&cargoPct>=0.10){for(const j of junk)actions.push({action:'jettison',ship:sym,symbol:j.symbol,units:j.units});continue;}

  // Navigate to mine
  if(wp!==MINE_WP)"""
    
    if old_navigate_mine in js:
        js = js.replace(old_navigate_mine, new_navigate_mine)
        print("    ✅ Added fuel-at-mine and junk-at-mine checks")
    else:
        print("    ⚠️ Could not find 'Navigate to mine' block")
    
    # FIX 2: In the "return to mine" block, add set_cruise before navigate
    # Find the return_to_mine navigate action and add cruise before it
    old_return = "actions.push({action:'navigate',ship:sym,waypoint:MINE_WP,reason:'return_to_mine',flightMode:'CRUISE'});continue;}}"
    new_return = "if(fm!=='CRUISE'){actions.push({action:'set_cruise',ship:sym});continue;}actions.push({action:'navigate',ship:sym,waypoint:MINE_WP,reason:'return_to_mine',flightMode:'CRUISE'});continue;}}"
    
    if old_return in js:
        js = js.replace(old_return, new_return)
        print("    ✅ Added set_cruise before return_to_mine navigate")
    else:
        print("    ⚠️ Could not find return_to_mine navigate")
    
    # FIX 3: In the "have trade ore -> navigate to deliver" block, add cruise
    old_deliver_nav = "actions.push({action:'navigate',ship:sym,waypoint:deliverDest,reason:'deliver',flightMode:'CRUISE'});continue;}if(status==='DOCKED')"
    new_deliver_nav = "if(fm!=='CRUISE'){actions.push({action:'set_cruise',ship:sym});continue;}actions.push({action:'navigate',ship:sym,waypoint:deliverDest,reason:'deliver',flightMode:'CRUISE'});continue;}if(status==='DOCKED')"
    
    if old_deliver_nav in js:
        js = js.replace(old_deliver_nav, new_deliver_nav)
        print("    ✅ Added set_cruise before deliver navigate")
    else:
        print("    ⚠️ Could not find deliver navigate")
    
    # FIX 4: In the "Navigate to mine" block (wp!==MINE_WP), add cruise
    old_mine_nav = "actions.push({action:'navigate',ship:sym,waypoint:MINE_WP,reason:'mine',flightMode:'CRUISE'});continue;}if(status==='DOCKED')"
    new_mine_nav = "if(fm!=='CRUISE'){actions.push({action:'set_cruise',ship:sym});continue;}actions.push({action:'navigate',ship:sym,waypoint:MINE_WP,reason:'mine',flightMode:'CRUISE'});continue;}if(status==='DOCKED')"
    
    if old_mine_nav in js:
        js = js.replace(old_mine_nav, new_mine_nav)
        print("    ✅ Added set_cruise before mine navigate")
    else:
        print("    ⚠️ Could not find mine navigate")
    
    # FIX 5: In the IN_TRANSIT skip, also handle DRIFT mode
    old_transit = "if(status==='IN_TRANSIT')continue;"
    new_transit = "if(status==='IN_TRANSIT'){if(fm==='DRIFT'){actions.push({action:'set_cruise',ship:sym});}continue;}"
    
    if old_transit in js:
        js = js.replace(old_transit, new_transit)
        print("    ✅ Added DRIFT->CRUISE for IN_TRANSIT ships")
    else:
        print("    ⚠️ Could not find IN_TRANSIT skip")
    
    return js


def main():
    print("=" * 60)
    print("ST-07 Mission Control Fix")
    print("=" * 60)
    
    # Backup database
    print(f"\nBacking up database to {BACKUP_PATH}...")
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print("  ✅ Backup done")
    
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    
    # Get all active ST-07 workflows
    cur.execute("""
        SELECT w.id, w.name, w.nodes 
        FROM workflow_entity w 
        WHERE w.name LIKE 'HERMES-%-ST-07' AND w.active = 1
        ORDER BY w.name
    """)
    workflows = cur.fetchall()
    
    print(f"\nFound {len(workflows)} active ST-07 workflows")
    
    for wf in workflows:
        name = wf['name']
        wid = wf['id']
        nodes = json.loads(wf['nodes'])
        
        print(f"\n{'=' * 60}")
        print(f"Processing: {name}")
        
        fixed = False
        for node in nodes:
            if node['name'] == 'Mission Control' and node['type'] == 'n8n-nodes-base.code':
                old_js = node['parameters'].get('jsCode', '')
                new_js = fix_mission_control(old_js)
                
                if old_js != new_js:
                    node['parameters']['jsCode'] = new_js
                    print(f"  Updated Mission Control ({len(old_js)} -> {len(new_js)} chars)")
                    fixed = True
                else:
                    print(f"  No changes needed")
                    fixed = True
                break
        
        if not fixed:
            print(f"  ⚠️ No Mission Control node found")
            continue
        
        # Update the workflow in the database
        updated_nodes = json.dumps(nodes)
        cur.execute("UPDATE workflow_entity SET nodes = ?, updatedAt = ? WHERE id = ?",
                    (updated_nodes, datetime.now().isoformat(), wid))
        print(f"  ✅ Updated in database")
    
    db.commit()
    db.close()
    
    print(f"\n{'=' * 60}")
    print("All workflows updated in database!")
    print("Restart n8n to apply changes: docker restart n8n-n8n-1")
    print("=" * 60)


if __name__ == "__main__":
    main()
