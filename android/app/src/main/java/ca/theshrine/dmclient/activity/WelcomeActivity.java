package ca.theshrine.dmclient.activity;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;

import ca.theshrine.dmclient.R;

public class WelcomeActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_welcome);
    }

    @Override
    protected void onResume() {
        super.onResume();

        // TODO: check list of recents to see what sessions we have
        TextView thing = (TextView)this.findViewById(R.id.recentSessionsTextLabel);
        thing.setText("No recent sessions.");
    }

    public void onFindNearbyGames(View view) {
        Intent intent = new Intent(this, LoadingActivity.class);
        this.startActivity(intent);
    }
}
