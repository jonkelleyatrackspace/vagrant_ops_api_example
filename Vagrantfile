# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # speeds up bad network
  config.vm.provider :virtualbox do |vb|
    # speedup
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
  end

  config.vm.box = "centos-7.0-x86_64"
  config.vm.box_url = "https://github.com/tommy-muehle/puppet-vagrant-boxes/releases/download/1.1.0/centos-7.0-x86_64.box"

  config.ssh.forward_agent = true
  config.ssh.insert_key = false
  config.hostmanager.enabled = true # vagrant plugin install vagrant-hostmanager
  config.cache.scope = :box         # vagrant plugin install vagrant-cachier

  # ------------
  # - API NODE - 
  # ------------
  # Perform the api functions
  config.vm.define "postgres-api" do |api|
    api.vm.hostname = "postgres"
    api.vm.network :private_network, ip: "172.21.12.12", auto_config: true
    api.vm.network "forwarded_port", guest: 80, host: "8080", auto_correct: true

    # The IP was reverting to dhcp... centos 7 issue?
    # http://stackoverflow.com/questions/32518591/centos7-with-private-network-lost-fixed-ip
    api.vm.provision :shell, :inline => "sudo nmcli connection reload", :privileged => true
    api.vm.provision :shell, :inline => "sudo systemctl restart network.service", :privileged => true

    api.vm.provision "ansible" do |ansible|
      #ansible.verbose = "vvvvv"
      ansible.playbook = "ansible-playbooks/postgres-api.yml"
    end
  end

  # -------------------
  # - ANSIBLE RUNHOST -
  # -------------------
  # Perform the ansible proxy examples
  config.vm.define "skyscraper" do |api|
    api.vm.hostname = "skyscraper"
    api.vm.network :private_network, ip: "172.21.12.13", auto_config: true
    api.vm.network "forwarded_port", guest: 80, host: "8080", auto_correct: true

    # The IP was reverting to dhcp... centos 7 issue?
    # http://stackoverflow.com/questions/32518591/centos7-with-private-network-lost-fixed-ip
    api.vm.provision :shell, :inline => "sudo nmcli connection reload", :privileged => true
    api.vm.provision :shell, :inline => "sudo systemctl restart network.service", :privileged => true

    api.vm.provision "ansible" do |ansible|
      #ansible.verbose = "vvvvv"
      ansible.playbook = "ansible-playbooks/ansibleskyscraper_install.yml"
    end
  end

  # ----------------------
  # - REPOSITORY EXAMPLE -
  # ----------------------
#  (1..3).each do |i|
#    config.vm.define "repo-n0#{i}" do |config|
#      config.vm.hostname = "repo-n0#{i}"
#      config.vm.network  :private_network, ip: "172.21.12.#{i+12}", auto_config: true
#      localport = [808, i].join.to_i
#      config.vm.network :forwarded_port, guest: 80, host: "#{localport}", auto_correct: true
#
#      # The IP was reverting to dhcp...
#      # http://stackoverflow.com/questions/32518591/centos7-with-private-network-lost-fixed-ip
#      config.vm.provision :shell, :inline => "sudo nmcli connection reload", :privileged => true
#      config.vm.provision :shell, :inline => "sudo systemctl restart network.service", :privileged => true
#
#      config.vm.provision "ansible" do |ansible|
#        ansible.verbose = "vvvvv"
#        ansible.playbook = "ansible-playbooks/repo_play.yml"
#      end
#    end
#  end
#end

end
