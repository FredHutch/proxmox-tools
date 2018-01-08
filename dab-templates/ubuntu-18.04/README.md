## Debian Jessie minimal Template

- based on Debootstrap minimal install
- adds Python for use with Ansible for example
- removes Postfix to make room for an alternate mail server
- temporarily permits root login with password for easy initialisation
  - intended to receive proper SSHD settings and keys via Ansible
- small 117 MB compressed template
- consumes about 250 MB on disk for a running container

## fixes for Ubuntu 18.04

- misses ifconfig binary
- create new tree rootfs-cp and put old ifconfig into rootfs-cp/sbin
- patch /uar/bin/dab so rootfs-cp tree is copied to rootfs before bootstrap
      +  use File::NCopy;

        $dab->ve_init();

      +  my $source_dir  = 'rootfs-cp';
      +  my $target_dir  = 'rootfs';
      +  my $cp = File::NCopy->new(recursive => 1);
      +  $cp->copy("$source_dir/*", $target_dir)
                   or die "Could not perform rcopy of $source_dir to $target_dir: $!";

        $dab->bootstrap ($opts);

- install file copy perl module: apt install libfile-ncopy-perl


and before you deploy make changes to :

/usr/share/perl5/PVE/LXC/Setup/Ubuntu.pm

