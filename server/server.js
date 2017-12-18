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
var db = new sqlite3.Database(path, function(err){
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
app.get("/", function(req, res){
    console.log(`${hashedPass} \t ${row.passwd}`);
    console.log("GET /");
    res.json({
        success: true,
        message: "server is running"
    });
});

//add a user
app.post("/users", function(req, res){
    var username = req.body.Username;
    var passwd = req.body.Passwd;
    console.log("Creating new user " + username +  "...");

    var hashedPass = crypto.createHash('md5').update(passwd).digest('hex');
    var query = `INSERT INTO users (user_name,password) VALUES( "${username}",`+ 
        `"${hashedPass}")`;
    db.run(query, function(err){
        if (err){
            console.error("failed to add user \n" + err.message);
            res.json({
                success: false,
                message: err.message
            });
        }
        else{
            console.log("user added successfully");
            res.json({
                success: true,
                message: "success"
            });
        }
    });
});

//authenticate an existing user
app.post("/authenticate", function(req,res){
    var username = req.body.Username;
    var passwd = req.body.Passwd;
    console.log("Authenticating user " + username +  "...");

    var hashedPass = crypto.createHash('md5').update(passwd).digest('hex'); 
    var query = `SELECT id, password FROM users WHERE user_name="${username}"`;
    db.get(query, function(err, row){
        if(err){
            console.error(err.message);
            res.json({
                success: false,
                message: err.message
            });
        }
        if(row == undefined){
            console.error(`user ${username} not found`);
            res.json({
                success: false,
                message: "user not found"
            });
        }
        if (row.password != hashedPass){
            console.error(`authentication of user ${username} failed`);
            res.json({
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
           res.json({
               success: true,
               message:  token
           });
        }

    });
});

app.get("/authenticate/check", verify, function(req, res){
    var decoded = req.decoded;
    console.log(`checked authentication for ${decoded.username}`);
    console.log(decoded);
    res.json({
        success: true,
        message: decoded.username
    });
});


////////////////////////////////////////////////////////////////////////////////
//                                SERVER START                                //
////////////////////////////////////////////////////////////////////////////////
app.listen(port, function(){
    console.log("dmtool server started on port " + port );
});

////////////////////////////////////////////////////////////////////////////////
//                            HELPERS AND MIDDLEWARE                          //
////////////////////////////////////////////////////////////////////////////////
function verify(req,res,next) {
    // check header or url parameters or post parameters for token
    var token = req.headers['token'];
    
    if (token) {
  
        // verifies secret and checks exp
        jwt.verify(token, app.get("authKey"), function(err, decoded) {      
            if (err) {
                console.error("request with invalid token");
                res.json({
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