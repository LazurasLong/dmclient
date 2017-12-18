--code to intitialise the database template

CREATE TABLE users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
   user_name TEXT NOT NULL,
    password TEXT NOT NULL);
    
    
CREATE TABLE systems (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
      author TEXT,
 description TEXT);
INSERT INTO systems (name, author, description)
     VALUES ('Dungeons and Dragons 5th edition', 'Wizards of the Coast', '5th edition of Dungeons and Dragons');
    
        
CREATE TABLE campaigns (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
      author INTEGER NOT NULL REFERENCES users,
      system INTEGER NOT NULL REFERENCES systems,
    password TEXT);
      
CREATE TABLE gms (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
        user INTEGER NOT NULL REFERENCES users,
    campaign INTEGER NOT NULL REFERENCES campaigns);
 
 
CREATE TABLE players (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
        user INTEGER NOT NULL REFERENCES users,
    campaign INTEGER NOT NULL REFERENCES campaigns);
    

CREATE TABLE player_characters (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
      player INTEGER NOT NULL REFERENCES players,
        name TEXT,
 description TEXT);
       
          
CREATE TABLE stats_5e (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
          author INTEGER NOT NULL REFERENCES users,
         private BOOLEAN NOT NULL, 
           class TEXT,
            race TEXT,
           level INTEGER,
             str INTEGER,
             dex INTEGER,
             con INTEGER,
             int INTEGER,
             wis INTEGER,
             cha INTEGER,
          max_hp INTEGER,
      prof_bonus INTEGER,
           speed INTEGER,
        str_save BOOLEAN,
        dex_save BOOLEAN,
        con_save BOOLEAN,
        int_save BOOLEAN,
        wis_save BOOLEAN,
        cha_save BOOLEAN,
       athletics BOOLEAN,
      acrobatics BOOLEAN,
         stealth BOOLEAN,
  slight_of_hand BOOLEAN,
          arcana BOOLEAN,
         history BOOLEAN,
   investigation BOOLEAN,
          nature BOOLEAN, 
        religion BOOLEAN,
animal_handleing BOOLEAN,
         insight BOOLEAN,
        medicine BOOLEAN,
      perception BOOLEAN,
       deception BOOLEAN,
      perfomance BOOLEAN,
    intimidation BOOLEAN,
      persuasion BOOLEAN,
   proficiencies TEXT,
      background TEXT,
        features TEXT,
 casting_ability TEXT,
spells_per_day_1 INTEGER,
spells_per_day_2 INTEGER,
spells_per_day_3 INTEGER,
spells_per_day_4 INTEGER,
spells_per_day_5 INTEGER,
spells_per_day_6 INTEGER,
spells_per_day_7 INTEGER,
spells_per_day_8 INTEGER,
spells_per_day_9 INTEGER,
        cantrips TEXT,
        spells_1 TEXT,
        spells_2 TEXT,
        spells_3 TEXT,
        spells_4 TEXT,
        spells_5 TEXT,
        spells_6 TEXT,
        spells_7 TEXT,
        spells_8 TEXT,
        spells_9 TEXT,
       languages TEXT);
        
       
CREATE TABLE pc_stats_5e ( 
                id INTEGER PRIMARY KEY AUTOINCREMENT,
  player_character INTEGER NOT NULL REFERENCES player_characters,
        stat_block INTEGER NOT NULL REFERENCES stats_5e,
             deity TEXT,
         alignment TEXT,
personality_traits TEXT,
            ideals TEXT,
             bonds TEXT,
             flaws TEXT,
         inventory TEXT);

      
CREATE TABLE npcs (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
       name TEXT,
   campaign INTEGER NOT NULL REFERENCES campaigns,
description TEXT);


CREATE TABLE npc_stats_5e (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
         npc INTEGER REFERENCES npcs,
  stat_block INTEGER REFERENCES stats_5e);
  

CREATE TABLE sessions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign INTEGER NOT NULL REFERENCES campaigns,
        date DATE);

        
CREATE TABLE session_attendees (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
     session INTEGER NOT NULL REFERENCES sessions,
   character INTEGER NOT NULL REFERENCES player_characters);


CREATE TABLE campaign_notes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign INTEGER NOT NULL REFERENCES campaigns,
      author INTEGER NOT NULL REFERENCES gms,
      hidden BOOLEAN,
        name TEXT,
        body TEXT); 
        
        
CREATE TABLE player_session_notes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
      author INTEGER NOT NULL REFERENCES players,
     session INTEGER NOT NULL REFERENCES sessions,
        body TEXT);
        
        
CREATE TABLE gm_session_notes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
      author INTEGER NOT NULL REFERENCES gms,
     session INTEGER NOT NULL REFERENCES sessions,
      hidden BOOLEAN,
       body TEXT);
      