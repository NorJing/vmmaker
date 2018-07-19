var express = require('express');
var app = express();
app.set('view engine', 'jade');
const bodyParser = require('body-parser');
// app.use(bodyParser.urlencoded( {extend: true} ));
// app.use(bodyParser.json());
app.use(bodyParser());
app.use(express.static('public'));
const { spawn } = require('child_process');
var fs = require('fs');
// var jsonfile = require('jsonfile');
var morgan = require('morgan');
// use morgan to log requests to the console
app.use(morgan('dev'));
var passwordHash = require('password-hash');

var run = 'False';
var username = 'admin';
var hashedPassword = 'sha1$9174d9cc$1$db21a2d048d32550277f66096da623fba74ada00';
var global_message = "";

function is_run(){
   return run;
}
 
app.get('/login', function(req, res){
   res.render('login');
})

app.post('/login', function(req, res){
   let username = req.body.username;
   let password = req.body.password;
   let loginwarning = 'Login fails. Please login again.';
   if (username == 'admin' && passwordHash.verify(password, hashedPassword)){
      console.log('login successfully!');
      run='True';
      res.redirect(303, '/create_vm/testenv');
   }else{
      console.log("loginwarning=" + loginwarning);
      res.render('login', { loginwarning: loginwarning });
   }
})

app.get('/create_vm/testenv', function(req, res) {
   if (is_run() == 'True'){
      console.log("/create_vm get create_vm");
      /* var ips = "";
      var file = './data/ips.json';
      jsonfile.readFile(file, function(err, obj) {
         // console.error(err);
         ips = obj;
         // print json file
         console.dir(ips);
         res.render('create_vm', {ips: ips});      
      })*/
      var mysql = require('mysql');
      var conn = mysql.createConnection({
         host: "localhost",
         user: "root",
         password: "strong_password",
         database: "ips"
      });
      conn.connect(function(err){
         if(err) throw err;
         conn.query("select * from testenv_ips", function(err, result, fields){
            if(err)
               console.log(err);
            else
               console.log(result);
               res.render('create_vm', {ips:result});
         });
      });
   }else{
      console.log('Get /create_vm/testenv fail.');
      res.send('Please login first. Go to localhost/login');
      // res.redirect(303, '/login');
   }
})

app.post('/create_vm/testenv', function(req, res) {
   console.log("/create_vm/testenv post create_vm/testenv");
   let hostname = req.body.hostname;
   let cluster = req.body.cluster;
   let datacenter = req.body.datacenter;
   let folder = String(req.body.folder).replace(/,/g, '');
   let resource_pool = req.body.resource_pool;
   let template = String(req.body.template).replace(/,/g, '');
   let datastore = String(req.body.datastore).replace(/,/g, '');
   let vm_ip = String(req.body.ip).replace(/_/g, '.');
   let vm_netmask = '255.255.255.0';
   let vm_gateway = String(req.body.gateway).replace(/_/g, '.');
   let networks = String(req.body.networks).replace(/,/g, '');
   let vm_disk_size_gb = '60';
   let vm_num_cpus = '2';
   let vm_memory_mb = '4096';
   let DNS1 = 'dns ip1';
   let DNS2 = 'dns ip2'; 
   let domain = '\"domain.1 domain.2\"';
   console.log("hostname=" + hostname);
   console.log("cluster=" + cluster);
   console.log("datacenter=" + datacenter);
   console.log("folder=" + folder);
   console.log("resource_pool=" + resource_pool);
   console.log("template=" + template);
   console.log("datastore=" + datastore);
   console.log("ip=" + vm_ip);
   console.log("networks=" + networks);
   let puppet_environment = req.body.puppet_environment;
   let vm_environment = req.body.vm_environment;
   console.log("puppet_environment=" + puppet_environment);
   console.log("vm_environment=" + vm_environment);
   let vm_config = "./create_vm/config/vm_config.yml";
   var writeStream = fs.createWriteStream(vm_config);
   writeStream.once('open', function(fd){
     writeStream.write("---\n");
     writeStream.write("vm_hostname: " + hostname + "\n");
     writeStream.write("cluster: " + cluster + "\n");
     writeStream.write("datacenter: " + datacenter + "\n");
     writeStream.write("folder: " + folder + "\n");
     writeStream.write("resource_pool: " + resource_pool + "\n");
     writeStream.write("template: " + template + "\n");
     writeStream.write("datastore: " + datastore + "\n");
     writeStream.write("vm_ip: " + vm_ip + "\n");
     writeStream.write("vm_netmask: " + vm_netmask + "\n");
     writeStream.write("vm_gateway: " + vm_gateway + "\n");
     writeStream.write("networks: " + networks + "\n");
     writeStream.write("vm_disk_size_gb: " + vm_disk_size_gb + "\n");
     writeStream.write("vm_num_cpus: " + vm_num_cpus + "\n");
     writeStream.write("vm_memory_mb: " + vm_memory_mb + "\n");
     writeStream.write("DNS1: " + DNS1 + "\n");
     writeStream.write("DNS2: " + DNS2 + "\n");
     writeStream.write("domain: " + domain + "\n");
     writeStream.write("puppet_master_fqdn: " + "my puppet master fqdn" + "\n");
     writeStream.write("domain_prefix: " + "my domain prefix" + "\n");
     writeStream.write("puppet_environment: " + puppet_environment + "\n");
     writeStream.write("vm_environment: " + vm_environment + "\n");
     writeStream.end();
     console.log("vm_config file written. Creating vm...");
   });
   var str = "";
   const command = spawn('ansible-playbook', ['create_vm/clone_vm.yml']);
   command.stdout.on('data', function(data){
     console.log("ansible stdout:");
     console.log(`${data}`);
     str = data.toString();
   });
   command.on('close', function(code){
      console.log("close:" + str);
   });
   command.on('exit', function(code){
      console.log("exit:" + str);
      global_message = "next step:";
      res.redirect(303, '/create_vm/update_dns');
   });
})

app.get('/create_vm/update_dns', function(req, res){
    if(is_run() == 'True'){
       console.log("get /create_vm/update_dns");
       global_message = "update_dns";
       var data = fs.readFileSync('create_vm/config/vm_config.yml', 'utf8');
       console.log(data);
       res.render('update_dns', {message:global_message, vm_data:data});
    }else{
       console.log('Get /create_vm/update_dns fail.');
       res.send('Please login first. Go to localhost/login');
    }
})

app.post('/create_vm/update_dns', function(req, res){
    console.log("post /create_vm/update_dns");
    var str2 = '';
    const command2 = spawn('python', ['create_vm/scripts/config_vm.py', 'update_dns']);
    command2.stdout.on('data', function(data){
        console.log("python stdout:");
        console.log(`${data}`);
        str2 = data.toString();
    });
    command2.on('close', function(code){
        if (str2 == ''){
          str2 = "str2 is empty";
          console.log(str2);
        }
    });
    command2.on('exit', function(code){
      res.redirect(303, '/create_vm/connect_puppet_master');
   });
})

app.get('/create_vm/connect_puppet_master', function(req, res){
    if(is_run() == 'True'){
       console.log("get /create_vm/connect_puppet_master");
       global_message = "connect_puppet_master";
       var data = fs.readFileSync('create_vm/config/vm_config.yml', 'utf8');
       console.log(data);
       res.render('connect_puppet_master', {message:global_message, vm_data:data});
    }else{
       console.log('Get /create_vm/connect_puppet_master fail.');
       res.send('Please login first. Go to localhost/login');
    }
})

app.post('/create_vm/connect_puppet_master', function(req, res){
    console.log("post /create_vm/connect_puppet_master");
    var str3 = '';
    const command3 = spawn('python', ['create_vm/scripts/config_vm.py', 'connect_puppet_master']);
    command3.stdout.on('data', function(data){
        console.log("python stdout:");
        console.log(`${data}`);
        str3 = data.toString();
    });
    command3.on('close', function(code){
        if (str3 == ''){
          str3 = "str3 is empty";
          console.log(str3);
        }
    });
    command3.on('exit', function(code){
      res.send("connect_puppet_master done");
   });
})

// testing code
app.get('/city', function(req, res) {
   console.log("get /city");
   res.render('city');
})

app.post('/city', function(req, res) {
   let city = req.body.city;
   res.render('city', {city: city});
})

// testing code
app.get('/test', function(req, res) {
   if ( run == 'True') {
      const output = spawn('ls', ['-lha', '/usr']);
      output.stdout.on('data', (data1) => {
        console.log(`stdout: ${data1}`);
        res.send(`stdout: ${data1}`);
      });
      output.stderr.on('data', (data1) => {
        console.log(`stderr: ${data1}`)
      });
   }else{
     console.log("run=" + run);
     res.send("run=" + run);
   }
})

var server = app.listen(80, function() {
   var host = server.address().address;
   var port = server.address().port;
   console.log("app at http://%s:%s", host, port);
})

