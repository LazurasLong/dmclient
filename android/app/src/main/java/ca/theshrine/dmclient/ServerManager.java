package ca.theshrine.dmclient;

/**
 * Still figuring out design, but this class allows server connections to
 * exist outside of the activities that might use them. This means that
 * events such as rotation do not close the connections.
 *
 * Expected that instances of this class are obtained from the DMApplication.
 */
public class ServerManager {
    public void sweepLan() {

    }
}
