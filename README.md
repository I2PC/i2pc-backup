# i2pc-backup

Distributed auto-updatable backup infrastructure.

## Dependencies

### Debian-based distros:

$ sudo apt-get install git wget rsync

### Windows

Download and install a base Cygwin system: https://www.cygwin.com/install.html

Important: Some mirrors contain old packages. In our tests, _mirrors.kernel.org_ worked well.

Now install dependencies of the script running CMD (Command Prompt):

```
> setup-x86_64.exe -q -P git,wget,rsync,cron,cygrunsrv
```

Now open a Cygwin terminal with administrative rights and run the wizard script `cron-config`:

```
$ cron-config
Do you want to install the cron daemon as a service? (yes/no) yes
Enter the value of CYGWIN for the daemon: [ ] ntsec
Do you want the cron daemon to run as yourself? (yes/no) no
are you using the cyglsa package ? (yes/no) no
Please enter the password for user 'cyg_server': SOMEPASSWORD
Reenter: SOMEPASSWORD
... no problem found.
```

You may also add cygwin to the path: System Properties -> Advanced -> Environment Variables -> Path -> Add "c:\cygwin64\bin"

Run the "Services" GUI windows app to check that the "Cron daemon" task is running.

## How it works

### Backup

Every machine has a name within the infrastructure backup. Let's see an example for the host `arquimedes`, which has name _arquimedes-linux_. When performing a backup, it would first get configuration files from [configs/arquimedes-linux](configs/arquimedes-linux):

  * [configs/arquimedes-linux/backup](configs/arquimedes-linux/backup): `RSYNC_MODULE FREQUENCY PATH1 PATH2 ... PATH3`
  * [configs/arquimedes-linux/cron](configs/arquimedes-linux/cron): Crontab entry.

So in this case, _arquimedes_ uses rsync module _arquimedes_. To get the backup host, the script would now check the file [configs/backup-hosts](configs/backup-hosts). In this case, it would match the entry `arquimedes faraday`, so the backup rsync endpoint is `faraday::arquimedes`.

`rsyncd.conf` must be configured on the backup server for this module:

```
[arquimedes]
        path = /nas/backup/computers/arquimedes
        hosts allow = arquimedes.cnb.csic.es
        write only = true
        read only = false
        list = false
        use chroot = true
```

### Update servers

Previously, update servers were used to store all the configuration files, but now we use directly this GitHub repository except for sensitive data that cannot be made public (for example, the email credentials).

### Auto-update

The script auto-updates itself and the configuration files pulling from this GitHub project (check [cron_scripts/rsync_backup_linux](cron_scripts/rsync_backup_linux), variables `repo_url`/`repo_branch`. Note that if there is a bug with the self-replacement code, you'll have to update manually the script on all clients.

## Notifications

If the script fails, it will try to send an email to cnb DOT notifications AT gmail.com. For this to work, you'll need a `sendemail.auth` file (see Setup section) on the backup servers and the package `sendemail` installed on every client.

### Logs

* On clients: `/var/log/rsync_backup.log`
* On backup servers: `/path/to/client/backup/rsync_backup.log`

## Setup

### Update servers

Create a file with the credentials for sendemail (Gmail account):

```
$ echo "EMAIL PASSWORD" > /etc/sysman/backup/sendemail.auth
```

For existing clients to get the new script you will also need to copy the new script:

```
$ git clone https://github.com/EyeSeeTea/i2pc-backup
$ cp i2pc-backup/cron_scripts/rsync_backup_linux /etc/sysman/backup
```

### Existing clients

The update mechanism should get the new script from the update servers without any additional action.

### New clients

You will need to install the script and the `sysconfig` file:

```
$ git clone https://github.com/EyeSeeTea/i2pc-backup
$ sudo mkdir -p /etc/cron_scripts
$ sudo install -m755 i2pc-backup/cron_scripts/rsync_backup_linux /etc/cron_scripts/
$ sudo echo "HOST-linux" > /etc/cron_scripts/sysconfig
```

Make sure you have also entries for `configs/HOST-linux` and `configs/backup-hosts`.