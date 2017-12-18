////////////////////////////////////////////////////////////////////////////////
//                                SETUP CODE                                  //
////////////////////////////////////////////////////////////////////////////////
var express = require("express");
var app = express();
var bodyParser = require("body-parser"); 
var jwt = require("jsonwebtoken");
var crypto = require("crypto");
var sqlite3 = require("sqlite3");
var config = require("./config");
var port = config.port;
var path = config.path;

console.log("connecting to database...")
var db = new sqlite3.Database(path, (err)=>{
    if (err){
        console.error(err.message);
        process.exit(1);
    }
    else{
    console.log("db connected successfully");
    }
});

app.set("authKey", config.key);
app.use(bodyParser.urlencoded({extended: true}));



////////////////////////////////////////////////////////////////////////////////
//                                   ROUTES                                   //
////////////////////////////////////////////////////////////////////////////////

//for checking server status
app.get("/", (req, res)=>{
    console.log("GET /");
    return res.json({
        success: true,
        message: "server is running"
    });
});

//add a user
app.post("/users", (req, res)=>{
    var username = req.body.Username;
    var passwd = req.body.Passwd;
    console.log("Creating new user " + username +  "...");

    var hashedPass = crypto.createHash('md5').update(passwd).digest('hex');
    var query = `INSERT INTO users (user_name,password) VALUES( "${username}",\ 
        "${hashedPass}")`;
    db.run(query, (err)=>{
        if (err){
            console.error("failed to add user \n" + err.message);
            return res.json({
                success: false,
                message: err.message
            });
        }
        else{
            console.log("user added successfully");
            return res.json({
                success: true,
                message: "success"
            });
        }
    });
});

//authenticate an existing user
app.post("/authenticate", (req,res)=>{
    var username = req.body.Username;
    var passwd = req.body.Passwd;
    console.log("Authenticating user " + username +  "...");

    var hashedPass = crypto.createHash('md5').update(passwd).digest('hex'); 
    var query = `SELECT id, password FROM users WHERE user_name="${username}"`;
    db.get(query, (err, row)=>{
        if(err){
            console.error(err.message);
            return res.json({
                success: false,
                message: err.message
            });
        }
        if(row == undefined){
            console.error(`user ${username} not found`);
            return res.json({
                success: false,
                message: "user not found"
            });
        }
        if (row.password != hashedPass){
            console.error(`authentication of user ${username} failed`);
            return res.json({
                success: false + decoded,
                message: "incorect password"
            });
        }
        else{
            var payload = {
                username: username,
                userId: row.id
            };
            var token = jwt.sign(payload, app.get("authKey"), {
                expiresIn: 60*60*24 //24 hours
           });
           console.log(`authenticated ${username} successfully`);
           return res.json({
               success: true,
               message:  token
           });
        }

    });
});

//check who is logged in
app.get("/authenticate/check", verify, (req, res)=>{
    var decoded = req.decoded;
    console.log(`checked authentication for ${decoded.username}`);
    console.log(decoded);
    return res.json({
        success: true,
        message: decoded.username
    });
});

//gets the currently supported systems
app.get("/systems", (req, res)=>{

    console.log("viewing supported systems");

    var query = "SELECT * FROM systems";
    db.all(query, (err, rows)=>{
        if (err){
            console.error(err.message);
            return res.json({
                success: false,
                message: err.message
            });
        }
        else if (rows.length == 0){
            console.error("systems is empty. This should not happen");
            return res.json({
                success: false,
                message: "There appear to be no supported systems, something \
                          is wrong."
            });  
        }
        else{
            return res.json({
                success: true,
                message: rows
            });
        }
    });
});

//create a campaign
app.post("/campaigns", verify, (req, res)=>{
    var userId = req.decoded.userId;
    var systemId = req.body.SystemId;
    var passwd = req.body.Passwd;
    var name = req.body.Name;

    var hashedPass = crypto.createHash('md5').update(passwd).digest('hex');

    var query = `INSERT INTO campaigns(author, system, name, password) VALUES`+
                `(${userId}, ${systemId}, "${name}", "${hashedPass}")`

    console.log(`${req.decoded.username} creating campaign ${name}`);
    db.serialize(()=>{
        db.run(query, (err)=>{
            if(err){
                console.error(`failed to add campaign. reason: ${err.message}`);
                return res.json({
                    success: false,
                    message: "duplicate campaign name for user"
                });
            }
            else{
                console.log(`campaign ${name} created. assigning author as gm`);
                query = `INSERT INTO gms (user, campaign)
                         SELECT ${userId},
                                c.id
                          FROM campaigns c
                         WHERE c.name = "${name}"
                           AND c.author = "${userId}"`;
                db.run(query, (err)=>{
                    if (err){
                        console.error(`failed to assign author as gm of `+
                        `campaign ${name}. removing campaign. reason: \n `+
                        `${err.message}`);

                        db.run(`DELETE FROM campaigns
                                 WHERE name = "${name}"
                                   AND author = "${userId}"`, 
                            (err)=>{
                                if (err){
                                    console.error(`WARNING: DATABASE IN ` +
                                    `INCONSISTENT STATE. \n FAILED TO REMOVE`+
                                    ` GMLESS CAMPAIGN ${name}\n THIS MAY`+
                                    ` REQUIRE MANUAL INTERVENTION.` + 
                                    `\n REASON: ${err.message}`);
                                    return res.json({
                                        success: false,
                                        message: "CRITICAL ERROR: DATABASE "+
                                        "INCONSISTENT"
                                    });
                                }
                            });

                        return res.json({
                            success: false,
                            message: err.message
                        });
                    }
                    else {
                        console.log(`assigned author as gm of campaign `+
                        `${name}`);
                        return res.json({
                            success: true,
                            message: "campaign added successfully"
                        });
                    }
                });
            }
        });
    });
});

////////////////////////////////////////////////////////////////////////////////
//                                SERVER START                                //
////////////////////////////////////////////////////////////////////////////////
app.listen(port, ()=>{
    console.log("dmtool server started on port " + port );
});

////////////////////////////////////////////////////////////////////////////////
//                            HELPERS AND MIDDLEWARE                          //
////////////////////////////////////////////////////////////////////////////////
function verify(req,res,next) {
    // check header for token
    var token = req.headers['token'];
    
    if (token) {
  
        // verifies secret and checks exp
        jwt.verify(token, app.get("authKey"), (err, decoded)=>{      
            if (err) {
                console.error("request with invalid token");
                return res.json({
                    success: false, 
                    message: 'Failed to authenticate token.' 
                });  
            }
        
            else {
                //save to request for use in other routes
                req.decoded = decoded;    
                next();
            }
        });
  
    } 
    
    else {
  
        // if there is no token
        // return an error
        console.error("request with no provided token");
        res.json({ 
            success: false, 
            message: 'No token provided.' 
        });
      
    }
}