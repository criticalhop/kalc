from tests.libs_for_tests import *

daemonset1_100_100_h 

#@pytest.mark.skip(reason="temporary skip")
def test_AnyGoal():
    k = KubernetesCluster()
    k.load(open(nodes1_2_940_2700).read())
    k.load(open(pods_1_100_100_h).read())
    k.load(open(pods_1_100_100_h_s1).read())

    k.load(open(pods_1_100_100_z).read())
    k.load(open(pods_1_100_100_z_s1).read())
    k.load(open(pods_1_100_100_z_s2).read()) 

    k.load(open(pods_1_500_1000_h).read())
    k.load(open(pods_1_500_1000_h_s1).read())

    k.load(open(pods_1_500_1000_z).read())
    k.load(open(pods_1_500_1000_z_s1).read())
    k.load(open(pods_1_500_1000_z_s2).read())
    k.load(open(priorityclass).read())
    k.load(open(service1).read())
    k.load(open(service2).read())

    k.create_resource(open(deployment2_5_100_100_h).read())
    k._build_state()
    p = AnyGoal(k.state_objects) # self.scheduler.status == STATUS_SCHED["Clean"]
    print_objects(k.state_objects)
    p.run(timeout=660, sessionName="test_AnyGoal")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    print_objects(k.state_objects)

#@pytest.mark.skip(reason="temporary skip")
def test_direct():
    args = []
    run(["--from-dir",nodes1_2_940_2700,"--from-dir", pods_1_100_100_h,"--from-dir", pods_1_100_100_h_s1,"--from-dir", pods_1_100_100_z,"--from-dir", pods_1_100_100_z_s1,"--from-dir", pods_1_100_100_z_s2,"--from-dir", pods_1_500_1000_h,"--from-dir", pods_1_500_1000_h_s1,"--from-dir", pods_1_500_1000_z,"--from-dir", pods_1_500_1000_z_s1,"--from-dir", pods_1_500_1000_z_s2,"--from-dir", priorityclass,"--from-dir", service1,"--from-dir", service2, "-f", deployment2_5_100_100_h, "-o", "yaml", "-t", "650"])
    print(result)
    

    # args=[]
    # args.extend(["--dump-file", " ".join([nodes1_2_940_2700, pods_1_100_100_h, pods_1_100_100_h_s1, pods_1_100_100_z, pods_1_100_100_z_s1, pods_1_100_100_z_s2, pods_1_500_1000_h, pods_1_500_1000_h_s1, pods_1_500_1000_z, pods_1_500_1000_z_s1, pods_1_500_1000_z_s2, priorityclass, service1, service2])])
    # args.extend(["-f", deployment2_5_100_100_h, "-o", "yaml", "--pipe"])



#@pytest.mark.skip(reason="temporary skip")
def test_test():
    runner = CliRunner()
    args=[]
    args.extend(["--from-dir",nodes1_2_940_2700,"--from-dir", pods_1_100_100_h,"--from-dir", pods_1_100_100_h_s1,"--from-dir", pods_1_100_100_z,"--from-dir", pods_1_100_100_z_s1,"--from-dir", pods_1_100_100_z_s2,"--from-dir", pods_1_500_1000_h,"--from-dir", pods_1_500_1000_h_s1,"--from-dir", pods_1_500_1000_z,"--from-dir", pods_1_500_1000_z_s1,"--from-dir", pods_1_500_1000_z_s2,"--from-dir", priorityclass,"--from-dir", service1,"--from-dir", service2])
    args.extend(["-f", deployment2_5_100_100_h, "-o", "yaml", "-t", "650","--pipe"])
    result = runner.invoke(run, ["--from-dir",nodes1_2_940_2700,"--from-dir", pods_1_100_100_h,"--from-dir", pods_1_100_100_h_s1,"--from-dir", pods_1_100_100_z,"--from-dir", pods_1_100_100_z_s1,"--from-dir", pods_1_100_100_z_s2,"--from-dir", pods_1_500_1000_h,"--from-dir", pods_1_500_1000_h_s1,"--from-dir", pods_1_500_1000_z,"--from-dir", pods_1_500_1000_z_s1,"--from-dir", pods_1_500_1000_z_s2,"--from-dir", priorityclass,"--from-dir", service1,"--from-dir", service2, "-f", deployment2_5_100_100_h, "-o", "yaml", "-t", "650"])
    global RESULT
    RESULT=result
    print(RESULT.output)
    assert result.exit_code == 0

def test_has_deployment_creates_daemonset__pods_evicted_pods_pending():
    k = KubernetesCluster()
    k.load(open(nodes1_2_940_2700).read())
    k.load(open(pods_1_100_100_h).read())
    k.load(open(pods_1_100_100_h_s1).read())

    k.load(open(pods_1_100_100_z).read())
    k.load(open(pods_1_100_100_z_s1).read())
    k.load(open(pods_1_100_100_z_s2).read()) 

    k.load(open(pods_1_500_1000_h).read())
    k.load(open(pods_1_500_1000_h_s1).read())

    k.load(open(pods_1_500_1000_z).read())
    k.load(open(pods_1_500_1000_z_s1).read())
    k.load(open(pods_1_500_1000_z_s2).read())
    k.load(open(priorityclass).read())
    k.load(open(service1).read())
    k.load(open(service2).read())
    k.load(open(deployment2_5_100_100_h).read())

    k.create_resource(open(daemonset1_500_1000_h).read())
    k._build_state()
    p = AnyGoal(k.state_objects) # self.scheduler.status == STATUS_SCHED["Clean"]
    print_objects(k.state_objects)
    p.run(timeout=660, sessionName="test_AnyGoal")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    print_objects(k.state_objects)


def test_creates_deployment_but_insufficient_resource__pods_pending():
    k = KubernetesCluster()
    k.load(open(nodes1_2_940_2700).read())
    k.load(open(pods_1_100_100_h).read())
    k.load(open(pods_1_100_100_h_s1).read())

    k.load(open(pods_1_100_100_z).read())
    k.load(open(pods_1_100_100_z_s1).read())
    k.load(open(pods_1_100_100_z_s2).read()) 

    k.load(open(pods_1_500_1000_h).read())
    k.load(open(pods_1_500_1000_h_s1).read())
    k.load(open(pods_1_500_1000_h_s2).read())

    k.load(open(pods_1_500_1000_z).read())
    k.load(open(pods_1_500_1000_z_s1).read())
    k.load(open(pods_1_500_1000_z_s2).read())
    k.load(open(priorityclass).read())
    k.load(open(service1).read())
    k.load(open(service2).read())
    k.load(open(deployment2_5_100_100_h).read())

    k.create_resource(open(deployment1_5_100_100_z).read())
    k._build_state()
    p = AnyGoal(k.state_objects) # self.scheduler.status == STATUS_SCHED["Clean"]
    print_objects(k.state_objects)
    p.run(timeout=660, sessionName="test_AnyGoal")
    if not p.plan:
         raise Exception("Could not solve %s" % p.__class__.__name__)
    print(Scenario(p.plan).asyaml())
    print_objects(k.state_objects)

# def creates_service_and_deployment_insufficient_resource__service_outage():
#     k = KubernetesCluster()
#     k.load(open(nodes1_2_940_2700).read())
#     k.load(open(pods_1_100_100_h).read())
#     k.load(open(pods_1_100_100_h_s1).read())

#     k.load(open(pods_1_100_100_z).read())
#     k.load(open(pods_1_100_100_z_s1).read())
#     k.load(open(pods_1_100_100_z_s2).read()) 

#     k.load(open(pods_1_500_1000_h).read())
#     k.load(open(pods_1_500_1000_h_s1).read())
#     k.load(open(pods_1_500_1000_h_s2).read())

#     k.load(open(pods_1_500_1000_z).read())
#     k.load(open(pods_1_500_1000_z_s1).read())
#     k.load(open(pods_1_500_1000_z_s2).read())
#     k.load(open(priorityclass).read())
#     k.load(open(service1).read())
#     k.load(open(service2).read())
#     k.load(open(deployment2_5_100_100_h).read())

#     k.create_resource(open(deployment1_5_100_100_z).read())
#     k._build_state()
#     p = AnyGoal(k.state_objects) # self.scheduler.status == STATUS_SCHED["Clean"]
#     print_objects(k.state_objects)
#     p.run(timeout=660, sessionName="test_AnyGoal")
#     if not p.plan:
#          raise Exception("Could not solve %s" % p.__class__.__name__)
#     print(Scenario(p.plan).asyaml())
#     print_objects(k.state_objects)