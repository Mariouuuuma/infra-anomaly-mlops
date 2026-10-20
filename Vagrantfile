Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-22.04"

  {
    "web01" => "192.168.56.11",
    "db01"  => "192.168.56.12"
  }.each do |name, ip|
    config.vm.define name do |node|
      node.vm.hostname = name
      node.vm.network "private_network", ip: ip

      node.vm.provider "vmware_desktop" do |v|
        v.vmx["displayname"] = name
        v.vmx["memsize"]     = "1024"
        v.vmx["numvcpus"]    = "1"
        v.gui = false
      end

      node.vm.provision "shell", path: "scripts/provision.sh", args: [name]
    end
  end
end