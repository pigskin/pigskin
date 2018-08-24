from pigskin.pigskin import pigskin

"""Just some BS tests to get the ball rolling"""

def test_agent():
    gp = pigskin()
    assert gp.user_agent == 'Firefox'
