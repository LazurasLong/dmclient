package ca.theshrine.dmclient.activity;

import android.app.Activity;
import android.os.Bundle;

import ca.theshrine.dmclient.DMApplication;
import ca.theshrine.dmclient.R;
import ca.theshrine.dmclient.ServerManager;

public class LoadingActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_loading);

        DMApplication app = (DMApplication)this.getApplication();
        ServerManager manager = app.getServerManager();
    }
}
